import abc
from abc import ABC
from typing import List
from enum import Enum
import warnings
import datetime
import logging

import hydrafloods as hf
from hydrafloods.geeutils import batch_export
import geemap.foliumap as geemap
import ee

from EO_Floods.dataset import Dataset, ImageryType, DATASETS
from EO_Floods.utils import coords_to_ee_geom, get_centroid, date_parser


log = logging.getLogger(__name__)


class providers(Enum):
    HYDRAFLOODS = "hydrafloods"
    GFM = "GFM"


class Provider(ABC):
    def __init__(
        self,
        datasets: List[Dataset],
        start_date: str,
        end_date: str,
        geometry: list,
    ) -> None:
        pass

    @abc.abstractproperty
    def info(self):
        pass

    @abc.abstractmethod
    def preview_data(self):
        pass

    @abc.abstractmethod
    def generate_flood_extents(self):
        pass

    @abc.abstractmethod
    def generate_flood_depths(self):
        pass

    @abc.abstractmethod
    def plot_flood_extents(self):
        pass

    @abc.abstractmethod
    def plot_flood_depths(self):
        pass

    @abc.abstractmethod
    def export_data(self):
        pass


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
        self.default_flood_extent_algorithm: (
            str
        ) = dataset.default_flood_extent_algorithm
        self.algorithm_params: dict = dataset.algorithm_params
        self.visual_params: dict = dataset.visual_params
        self.obj: hf.Dataset = HF_datasets[dataset.name](
            region=region, start_time=start_date, end_time=end_date, **kwargs
        )
        log.debug(f"Initialized hydrafloods dataset for {self.name}")

        # col_size = self.obj.n_images
        # self.obj.collection = _mosaic_same_date_images(
        #     self.obj.collection, size=col_size
        # )


class HydraFloods(Provider):
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

    @property
    def info(self) -> List[dict]:
        """Information on the given datasets for the given temporal and spatial resolution.

        Returns
        -------
        List[dict]
            List of dictionaries containing information on the datasets.

        """
        dataset_info = []
        for dataset in self.datasets:
            dataset_info.append(
                {
                    "Name": dataset.name,
                    "Dataset ID": dataset.obj.asset_id,
                    "Number of images": dataset.obj.n_images,
                    "Dates": dataset.obj.dates,
                }
            )
        return dataset_info

    def preview_data(self, zoom=8) -> geemap.Map:
        """Previews the data by plotting it on a geemap.Map object per date of the image.

        Parameters
        ----------
        zoom : int, optional
            zoom level of map window, by default 8

        Returns
        -------
        geemap.Map
            Map object containing the mapped datasets per date
        """
        Map = geemap.Map(center=self.centroid, zoom=zoom)
        for dataset in self.datasets:
            dates = dataset.obj.dates
            for date in dates:
                d = ee.Date(date_parser(date))
                img = dataset.obj.collection.filterDate(d, d.advance(1, "day"))
                Map.add_layer(
                    img,
                    vis_params=dataset.visual_params,
                    name=f"{dataset.name} {date}",
                )
        return Map

    def select_data(
        self,
        datasets: List[str] | str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> List[dict]:
        """Select data that is suitable for generating flood extents. Selection can
        be made based on the dataset name and time range.

        Parameters
        ----------
        datasets : List[str] | str, optional
            name(s) of dataset(s) to select data for, by default None.
        start_date : str, optional
            Start date of time window of interest, by default None
        end_date : str, optional
            End date of time window interest, end date is exclusive, by default None,

        Returns
        -------
        List[dict]
            Returning Hydrafloods.info on the selected data
        """
        if isinstance(datasets, str):
            datasets = [datasets]

        if start_date and (start_date == end_date):
            log.warning("End date should be exclusive, setting end date to a day later")
            end_date = datetime.datetime.strftime(
                date_parser(end_date) + datetime.timedelta(days=1), "%Y-%m-%d"
            )

        if not all([start_date, end_date]):
            log.info(
                "No start date or end date were given, defaulting to "
                f"original start and end date: {self.start_date}, {self.end_date}"
            )
            start_date = self.start_date
            end_date = self.end_date

        if not datasets:
            datasets = [dataset.name for dataset in self.datasets]

        self.datasets = [
            HydraFloodsDataset(
                DATASETS[dataset_name], self.geometry, start_date, end_date
            )
            for dataset_name in datasets
        ]
        return self.info

    def generate_flood_extents(self, clip_ocean: bool = True) -> None:
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
            log.info(f"Generating flood extents for {dataset.name} dataset")
            if dataset.obj.n_images < 1:
                warnings.warn(
                    f"{dataset.name} has no images for date range {self.start_date} - {self.end_date}.",
                    UserWarning,
                )
                continue
            if clip_ocean:
                log.info("Clipping image to country boundaries")
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
                log.debug(f"Calculating MNDWI for {dataset.name}")
                dataset.obj.apply_func(
                    hf.add_indices,
                    indices=[dataset.algorithm_params["edge_otsu"]["band"]],
                    inplace=True,
                )
                dataset.obj.apply_func(
                    lambda x: x.cast({"mndwi": "double"}), inplace=True
                )
            log.info("Applying edge-otsu thresholding")
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

    def plot_flood_extents(self, zoom: int = 8) -> geemap.Map:
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
                log.info(
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
                log.info(
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


class GFM(Provider):
    def init():
        raise NotImplementedError
