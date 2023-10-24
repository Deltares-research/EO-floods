from typing import Union, Literal, Optional

import hydrafloods as hf
import ee
import geemap.foliumap as geemap

from EO_Floods.interface.floodmap import FloodMap
from EO_Floods.utils import (
    coords_to_ee_geom,
    filter_ee_imgcollection_by_geom,
    date_parser,
)


class FloodMapHF(FloodMap):
    def __init__(
        self,
        geometry: list,
        start_date: str,
        end_date: str,
        dataset: Union[str, ee.ImageCollection],
        imagery_type: Optional[Literal["SAR", "optical"]] = None,
        **dataset_kwargs
    ) -> None:
        self.geometry = coords_to_ee_geom(geometry)
        self.start_date = start_date
        self.end_date = end_date
        self.centroid = self.geometry.centroid(maxError=1).getInfo()["coordinates"]
        self.imagery_type = imagery_type

        hf_datasets = {
            "Sentinel 1": {
                "dataset": hf.Sentinel1,
                "imagery_type": "SAR",
                "band": "VV",
            },
            "Sentinel 2": {
                "dataset": hf.Sentinel2,
                "imagery_type": "optical",
                "band": "mndwi",
            },
            "Landsat 8": {
                "dataset": hf.Landsat8,
                "imagery_type": "optical",
                "band": "mndwi",
            },
            "Landsat 7": {
                "dataset": hf.Landsat7,
                "imagery_type": "optical",
                "band": "mndwi",
            },
            "VIIRS": {"dataset": hf.Viirs, "imagery_type": "optical", "band": "mndwi"},
            "MODIS": {"dataset": hf.Modis, "imagery_type": "optical", "band": "mndwi"},
        }
        if dataset in hf_datasets:
            self.dataset_type = "hf_dataset"
            self.dataset = hf_datasets[dataset]["dataset"](
                region=self.geometry,
                start_time=self.start_date,
                end_time=self.end_date,
                **dataset_kwargs
            )
            self.band = hf_datasets[dataset]["band"]
            self.imagery_type = hf_datasets[dataset]["imagery_type"]
        elif isinstance(dataset, ee.ImageCollection):
            self.dataset_type = "ee.ImageCollection"
            imgcollection = filter_ee_imgcollection_by_geom(
                dataset, start_date, end_date, self.geometry
            )
            self.dataset = hf.Dataset.from_imgcollection(
                imgcollection, **dataset_kwargs
            )
            self.band = None
            if self.imagery_type not in ["SAR", "optical"]:
                raise ValueError(
                    "Please specify whether the the given ImageColletion is of the 'SAR' or 'optical' imagery_type"
                )
        else:
            raise ValueError(
                "Given dataset is not a Hydrafloods dataset or an ee.ImageCollection"
            )

    @property
    def info(self):
        return {
            "dataset_id": self.dataset.asset_id,
            "n_images": self.dataset.n_images,
            "dates": self.dataset.dates,
        }

    def preview_data(
        self, dates: list = None, visParams: dict = {}, zoom: int = 7
    ) -> geemap.Map:
        # Retrieve center lat lon coordinates of input geometry
        centroid_latlon = [self.centroid[1], self.centroid[0]]
        return _map_data_by_dates(
            dataset=self.dataset,
            center=centroid_latlon,
            visParams=visParams,
            zoom=zoom,
            dates=dates,
        )

    def generate_flood_extents(
        self, band: str = None, clip_ocean: bool = True, **edge_otsu_options
    ) -> geemap.Map:
        dataset = self.dataset
        band = self.band if self.band else band
        # Clip input geometry with country borders in order to filter out ocean
        if clip_ocean:
            country_boundary = (
                ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0")
                .filterBounds(self.geometry)
                .first()
                .geometry()
            )
            clipped_data = self.dataset.collection.map(
                lambda img: img.clip(country_boundary)
            )
            dataset = hf.Dataset.from_imgcollection(clipped_data)
        if self.imagery_type == "optical":
            dataset = dataset.apply_func(hf.add_indices, indices=["mndwi"])
            flood_extent_maps = dataset.apply_func(
                hf.edge_otsu, band=band, **edge_otsu_options
            )
        else:
            flood_extent_maps = dataset.apply_func(
                hf.edge_otsu, band=band, **edge_otsu_options
            )
        self.flood_extents = flood_extent_maps

    def plot_flood_extents(
        self,
        dates: Optional[list] = None,
        visParams: dict = {
            "min": 0,
            "max": 1,
            "palette": ["#c0c0c0", "#000080"],
            "dimensions": 2000,
        },
        zoom: int = 7,
    ):
        if not hasattr(self, "flood_extents"):
            raise RuntimeError(
                "generate_flood_extents() needs to be called before calling this method"
            )
        center = [self.centroid[1], self.centroid[0]]
        return _map_data_by_dates(
            dataset=self.flood_extents,
            visParams=visParams,
            center=center,
            zoom=zoom,
            dates=dates,
        )

    def flood_depths(self):
        raise NotImplementedError

    def maximum_extent(self):
        raise NotImplementedError

    def maximum_duration(self):
        raise NotImplementedError

    def maximum_depth(self):
        raise NotImplementedError

    def metrics(self):
        raise NotImplementedError

    def export_data(self):
        raise NotImplementedError


@staticmethod
def _map_data_by_dates(
    dataset: hf.Dataset,
    visParams: dict,
    center: list,
    zoom: int,
    dates: Optional[list] = None,
) -> geemap.Map:
    Map = geemap.Map(center=center, zoom=zoom)
    if not dates:
        dates = dataset.dates
    for date in dates:
        img = dataset.collection.filter(ee.Filter.date(date_parser(date))).first()
        Map.add_layer(img, visParams, date)
    return Map
