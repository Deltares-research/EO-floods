from typing import List, Optional
import warnings
import datetime
import logging
import re

import hydrafloods as hf
from hydrafloods.geeutils import batch_export
import geemap.foliumap as geemap
import ee
import multiprocessing.pool
from tabulate import tabulate

from EO_Floods.dataset import Dataset, ImageryType, DATASETS
from EO_Floods.utils import (
    coords_to_ee_geom,
    get_centroid,
    date_parser,
    calc_quality_score,
)
from EO_Floods.providers import ProviderBase

logger = logging.getLogger(__name__)


class HydraFloods(ProviderBase):
    def __init__(
        self,
        datasets: List[Dataset],
        start_date: str,
        end_date: str,
        geometry: List[float],
        **kwargs,
    ) -> None:
        """Provider class for Hydrafloods

        Parameters
        ----------
        datasets : List[Dataset]
            List containing EO_Floods.Dataset objects with dataset information and
            configuration for processing.
        start_date : str
            Start date of the time window of interest (YYY-mm-dd).
        end_date : str
            End date of the time window of interest (YYY-mm-dd).
        geometry : List[float]
            List of coordinates of a bounding box in the [xmin, ymin, xmax, ymax] format.
            Coordinates should be in wgs84 (epsg:4326).
        """
        self.centroid = get_centroid(geometry)
        self.geometry = coords_to_ee_geom(geometry)
        self.start_date = start_date
        self.end_date = end_date
        self.initial_datasets = datasets
        self.datasets = [
            HydraFloodsDataset(dataset, self.geometry, start_date, end_date, **kwargs)
            for dataset in datasets
        ]

    def available_data(self) -> None:
        """Information on the given datasets for the given temporal and spatial resolution.

        Returns
        -------
        List[dict]
            List of dictionaries containing information on the datasets.

        """
        line0 = f"{'='*70}\n"
        output = ""
        for dataset in self.datasets:
            output += line0
            output += f"Dataset name: {dataset.name}\n"
            n_images = dataset.obj.n_images
            output += f"Number of images: {n_images}\n"
            output += f"Dataset ID: {dataset.obj.asset_id}\n\n"

            if n_images > 0:
                dates = dataset.obj.dates
                qa_scores = dataset._calc_quality_score()
                table_list = [[x, y] for x, y in zip(dates, qa_scores)]
                table = tabulate(
                    table_list,
                    headers=["Timestamp", "Quality score (%)"],
                    tablefmt="orgtbl",
                )
                output += table + "\n\n"

        print(output)

    def view_data(
        self,
        zoom: int = 8,
        dates: Optional[List[str] | str] = None,
        vis_params: dict = {},
    ) -> geemap.Map:
        """View data on a geemap instance. This can be used to visually check if
        the quality of the data is sufficient for further processing to flood maps.
        The data can be filtered based on date. In addition, visual parameters can
        be added as a dictionary with the dataset name as its key.

        Parameters
        ----------
        zoom : int, optional
            zoom level, by default 8
        dates : Optional[List[str]  |  str], optional
            A subselection of dates to , by default None
        vis_params : dict, optional
            A dictionary describing the visual parameters for each dataset, by default {}

        Returns
        -------
        geemap.Map
            a geemap.Map instance to visualize in a jupyter notebook
        """
        Map = geemap.Map(center=self.centroid, zoom=zoom)
        if isinstance(dates, str):
            dates = [dates]

        for dataset in self.datasets:
            if dates is None:
                dates = dataset.obj.dates
            for date in dates:
                img = _filter_collection_by_dates(date, dataset)
                Map.add_layer(
                    img,
                    vis_params=vis_params.get(
                        dataset.name, dataset.visual_params
                    ),  # If no vis_params are given take the default visual params for the dataset objects
                    name=f"{dataset.name} {date}",
                )
        return Map

    def generate_flood_extents(self, dates, clip_ocean: bool = True) -> None:
        """Generates flood extents on the selected datasets and for the given temporal
        and spatial resolution.

        Parameters
        ----------
        clip_ocean : bool, optional
            Option for clipping ocean pixels from the images. Ocean pixels can negatively
            influence the edge otsu algorithm. The clipping is done by using country
            borders, so be aware when your region of interest is across country
            boundaries. By default True.
        """
        flood_extents = {}
        for dataset in self.datasets:
            logger.info(f"Generating flood extents for {dataset.name} dataset")
            if dataset.obj.n_images < 1:
                warnings.warn(
                    f"{dataset.name} has no images for date range {self.start_date} - {self.end_date}.",
                    UserWarning,
                )
                continue
            if dates:
                imgs = []
                for date in dates:
                    imgs.append(_filter_collection_by_dates(date, dataset))
                dataset.obj = hf.Dataset.from_imgcollection(ee.ImageCollection(imgs))

            if clip_ocean:
                logger.info("Clipping image to country boundaries")
                country_boundary = (
                    ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0")
                    .filterBounds(self.geometry)
                    .first()
                    .geometry()
                )

                clipped_data = dataset.obj.collection.map(
                    lambda img: img.clip(country_boundary)
                )
                dataset.obj = hf.Dataset.from_imgcollection(clipped_data)
            if dataset.imagery_type == ImageryType.OPTICAL:
                logger.debug(f"Calculating MNDWI for {dataset.name}")
                dataset.obj.apply_func(
                    hf.add_indices,
                    indices=[dataset.algorithm_params["edge_otsu"]["band"]],
                    inplace=True,
                )
                dataset.obj.apply_func(
                    lambda x: x.cast({"mndwi": "double"}), inplace=True
                )
            logger.info("Applying edge-otsu thresholding")
            flood_extent = dataset.obj.apply_func(
                hf.edge_otsu, **dataset.algorithm_params["edge_otsu"]
            )

            # Invert values of flood extent so that water=1, land=0
            flood_extent = flood_extent.apply_func(
                lambda x: x.eq(0).copyProperties(x, ["system:time_start"])
            )

            flood_extents[dataset.name] = flood_extent
        self.flood_extents = flood_extents

    def generate_flood_depths(self):
        pass

    def plot_flood_extents(self, timeout: int = 60, zoom: int = 8) -> geemap.Map:
        """Plots the flood extents on a geemap.Map object.

        Parameters
        ----------
        zoom : int, optional
            Zoom level of the map window, by default 8

        Returns
        -------
        geemap.Map
            Map containing the flood extents and the data the flood extents are
            based on.

        """

        def _plot_flood_extents(zoom: int):
            if not hasattr(self, "flood_extents"):
                raise RuntimeError(
                    "generate_flood_extents() needs to be called before calling this method"
                )

            flood_extent_vis_params = {
                "bands": ["water"],
                "min": 0,
                "max": 1,
                "palette": ["#C0C0C0", "#000080"],
            }
            map = self.preview_data()
            for ds_name in self.flood_extents:
                for date in self.flood_extents[ds_name].dates:
                    d = ee.Date(date_parser(date))
                    img = (
                        self.flood_extents[ds_name]
                        .collection.filterDate(d, d.advance(1, "day"))
                        .mode()
                    )
                    map.add_layer(
                        img,
                        vis_params=flood_extent_vis_params,
                        name=f"{ds_name} {date} flood extent",
                    )
                max_extent_img = self.flood_extents[ds_name].collection.max()
                map.add_layer(
                    max_extent_img,
                    vis_params=flood_extent_vis_params,
                    name=f"{ds_name} max flood extent",
                )
            return map

        try:
            with multiprocessing.pool.ThreadPool() as pool:
                return_value = pool.apply_async(_plot_flood_extents, (zoom,)).get(
                    timeout=timeout
                )
        except multiprocessing.TimeoutError:
            raise TimeoutError(
                "Plotting floodmaps has timed out, increase the time out threshold or plot a smaller selection of your data"
            )
        return return_value

    def plot_flood_depths(self):
        pass

    def export_data(
        self,
        export_type: str = "toDrive",
        include_base_data: bool = False,
        folder: str = None,
        ee_asset_path: str = "",
        scale: int | float = None,
        **kwargs,
    ):
        """Exports the data generated in the floodmapping workflow to a Google Drive
        or as Earth Engine asset.

        Parameters
        ----------
        export_type : str, optional
            Two options for exporting data: "toAsset", "toDrive", by default "toDrive"
        include_base_data : bool, optional
            The base data can be exported as well. Be aware that this data is often
            of a large size and takes a long time to export, by default False.
        folder : str, optional
            Name of folder on Google Drive to export the data to, by default None
        ee_asset_path : str, optional
            Earth Engine path to export the data to, by default ""
        scale : int or float, optional
            Scale (resolution) in meters at which the image is exported, by default
            the scale of the flood extent image.
        """
        if export_type == "toDrive":
            folder = "EO_Floods"

        if hasattr(self, "flood_extents"):
            for ds in self.flood_extents.keys():
                logger.info(
                    f"Exporting {ds} flood extents {export_type[:2]+' '+export_type[2:]}"
                )

                if not scale:
                    scale = (
                        self.flood_extents[ds]
                        .collection.first()
                        .select("water")
                        .projection()
                        .nominalScale(),
                    )
                batch_export(
                    collection=self.flood_extents[ds].collection,
                    collection_asset=ee_asset_path,
                    export_type=export_type,
                    folder=folder,
                    suffix=f"{ds.replace(' ', '_')}_flood_extent",
                    scale=scale,
                    **kwargs,
                )
        else:
            raise RuntimeError(
                "First call generate_flood_extents() before calling export_data()"
            )
        if include_base_data:
            for dataset in self.datasets:
                logger.info(
                    f"Exporting {dataset.name} {export_type[:2]+' '+export_type[2:]}"
                )
                batch_export(
                    collection=dataset.obj.collection,
                    collection_asset=ee_asset_path
                    + f"{dataset.short_name}_EO_Floodmap",
                    export_type=export_type,
                    folder=folder,
                    region=dataset.obj.collection.geometry(),
                    suffix=dataset.short_name,
                    scale=dataset.obj.collection.first()
                    .select(1)
                    .projection()
                    .nominalScale(),
                    **kwargs,
                )


def _filter_collection_by_dates(date: str, dataset: HydraFloodsDataset):
    d = ee.Date(date_parser(date))
    if re.findall(r"(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$", date):
        img = dataset.obj.collection.filterDate(d, d.advance(1, "second"))
    else:
        img = dataset.obj.collection.filterDate(d, d.advance(1, "day")).mosaic()
    return img


class HydraFloodsDataset:
    def __init__(
        self,
        dataset: Dataset,
        region: ee.geometry.Geometry,
        start_date: str,
        end_date: str,
        **kwargs,
    ):
        """Class for initializing Hydrafloods datasets.

        Parameters
        ----------
        dataset : Dataset
            EO_Floods.Dataset object containing information on the dataset and configuration
            for processing.
        region : ee.geometry.Geometry
            Earth Engine geometry that represents the area of interest.
        start_date : str
            Start date of the time window of interest (YYY-mm-dd).
        end_date : str
            End date of the time window of interest (YYY-mm-dd).
        """
        HF_datasets = {
            "Sentinel-1": hf.Sentinel1,
            "Sentinel-2": hf.Sentinel2,
            "Landsat 7": hf.Landsat7,
            "Landsat 8": hf.Landsat8,
            "VIIRS": hf.Viirs,
            "MODIS": hf.Modis,
        }
        self.name: str = dataset.name
        self.short_name: str = dataset.short_name
        self.imagery_type: ImageryType = dataset.imagery_type
        self.default_flood_extent_algorithm: str = (
            dataset.default_flood_extent_algorithm
        )
        self.region = region
        self.qa_band = dataset.qa_band
        self.algorithm_params: dict = dataset.algorithm_params
        self.visual_params: dict = dataset.visual_params
        self.obj: hf.Dataset = HF_datasets[dataset.name](
            region=region, start_time=start_date, end_time=end_date, **kwargs
        )
        logger.debug(f"Initialized hydrafloods dataset for {self.name}")

        # col_size = self.obj.n_images
        # self.obj.collection = _mosaic_same_date_images(
        #     self.obj.collection, size=col_size
        # )

    def _calc_quality_score(self) -> List[float]:
        if (
            self.name in ["VIIRS", "MODIS"]
        ):  # these datasets consist of global images, need to be clipped first before reducing
            self.obj.apply_func(func=lambda x: x.clip(self.region), inplace=True)
        self.obj.apply_func(func=calc_quality_score, inplace=True, band=self.qa_band)
        qa_score = self.obj.collection.aggregate_array("qa_score").getInfo()
        return [round(score, 2) for score in qa_score]


def _mosaic_same_date_images(imgcol: ee.ImageCollection, size: int):
    imlist = imgcol.toList(size)

    unique_dates = imlist.map(
        lambda x: ee.Image(x).date().format("YYYY-MM-dd")
    ).distinct()

    def _mosaic_dates(d):
        d = ee.Date(d)
        img_props = imgcol.filterDate(d, d.advance(1, "day")).first()
        img = imgcol.filterDate(d, d.advance(1, "day")).mosaic()
        img = img.copyProperties(img_props, ["system:time_start", "system:id"])
        return img

    return ee.ImageCollection(unique_dates.map(_mosaic_dates))
