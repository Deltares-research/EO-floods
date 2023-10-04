from typing import Union

import hydrafloods as hf
import ee
import geemap.foliumap as geemap

from EO_Floods.interface.floodmap import FloodMap
from EO_Floods.utils import coords_to_ee_geom, filter_ee_imgcollection, decode_date


class FloodMapHF(FloodMap):
    def __init__(
        self,
        geometry: list,
        start_date: str,
        end_date: str,
        dataset: Union[str, ee.ImageCollection],
        **dataset_kwargs
    ) -> None:
        self.geometry = coords_to_ee_geom(geometry)
        self.start_date = start_date
        self.end_date = end_date

        hf_datasets = {
            "Sentinel 1": hf.Sentinel1,
            "Sentinel 2": hf.Sentinel2,
            "Landsat 8": hf.Landsat8,
            "Landsat 7": hf.Landsat7,
            "VIIRS": hf.Viirs,
            "MODIS": hf.Modis,
        }
        if dataset in hf_datasets:
            self.dataset_type = "hf_dataset"
            self.dataset = hf_datasets[dataset](
                region=self.geometry,
                start_time=self.start_date,
                end_time=self.end_date,
                **dataset_kwargs
            )
        elif isinstance(dataset, ee.ImageCollection):
            self.dataset_type = "ee.ImageCollection"
            imgcollection = filter_ee_imgcollection(
                dataset, start_date, end_date, self.geometry
            )
            self.dataset = hf.Dataset.from_imgcollection(
                imgcollection, **dataset_kwargs
            )
        else:
            raise ValueError(
                "Given dataset is not a Hydrafloods dataset or an" " ee.ImageCollection"
            )

    @property
    def info(self):
        return {
            "dataset_id": self.dataset.asset_id,
            "n_images": self.dataset.n_images,
            "dates": self.dataset.dates,
        }

    def preview_data(
        self, dates: list = None, vis_params: dict = {}, zoom: int = 7
    ) -> geemap.Map:
        # Retrieve center lat lon coordinates of input geometry
        centroid = self.geometry.centroid(maxError=1).getInfo()["coordinates"]
        centroid_latlon = [centroid[1], centroid[0]]
        Map = geemap.Map(center=centroid_latlon, zoom=zoom)
        if not dates:
            dates = self.dataset.dates
        for date in dates:
            img = self.dataset.collection.filter(
                ee.Filter.date(decode_date(date))
            ).first()
            Map.add_layer(img, vis_params, date)
        return Map

    def flood_extents(self, band=None):
        pass

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
