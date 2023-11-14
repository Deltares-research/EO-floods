import abc
from abc import ABC
from typing import List, Optional
from enum import Enum
import warnings
import datetime

import hydrafloods as hf
import geemap.foliumap as geemap
import ee

from EO_Floods.dataset import Dataset, ImageryType, DATASETS
from EO_Floods.utils import coords_to_ee_geom, get_centroid, date_parser
from EO_Floods.config import settings


class providers(Enum):
    HYDRAFLOODS = "hydrafloods"
    GFM = "GFM"


class Provider(ABC):
    def __init__(
        self,
        credentials,
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


class HydraFloodsDataset:
    def __init__(
        self,
        dataset: Dataset,
        region: ee.geometry.Geometry,
        start_date: str,
        end_date: str,
    ):
        HF_datasets = {
            "Sentinel-1": hf.Sentinel1,
            "Sentinel-2": hf.Sentinel2,
            "Landsat 7": hf.Landsat7,
            "Landsat 8": hf.Landsat8,
            "VIIRS": hf.Viirs,
            "MODIS": hf.Modis,
        }
        self.name: str = dataset.name
        self.imagery_type: ImageryType = dataset.imagery_type
        self.default_flood_extent_algorithm: (
            str
        ) = dataset.default_flood_extent_algorithm
        self.algorithm_params: dict = dataset.algorithm_params
        self.visual_params: dict = dataset.visual_params
        self.obj: hf.Dataset = HF_datasets[dataset.name](
            region=region, start_time=start_date, end_time=end_date
        )


class HydraFloods(Provider):
    def __init__(
        self,
        credentials: dict,
        datasets: List[Dataset],
        start_date: str,
        end_date: str,
        geometry: List[float],
    ) -> None:
        self.centroid = get_centroid(geometry)
        self.geometry = coords_to_ee_geom(geometry)
        self.start_date = start_date
        self.end_date = end_date
        self.initial_datasets = datasets
        self.datasets = [
            HydraFloodsDataset(dataset, self.geometry, start_date, end_date)
            for dataset in datasets
        ]

    @property
    def info(self) -> List[dict]:
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

    def preview_data(self, zoom=7) -> geemap.Map:
        Map = geemap.Map(center=self.centroid, zoom=zoom)
        for dataset in self.datasets:
            dates = dataset.obj.dates
            for date in dates:
                img = dataset.obj.collection.filter(ee.Filter.date(date_parser(date)))
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
        if isinstance(datasets, str):
            datasets = [datasets]

        if not all([start_date, end_date]):
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
        flood_extents = {}
        for dataset in self.datasets:
            if dataset.obj.n_images < 1:
                warnings.warn(
                    f"{dataset.name} has no images for date range {self.start_date} - {self.end_date}.",
                    UserWarning,
                )
                continue
            if clip_ocean:
                country_boundary = (
                    settings.country_boundaries_dataset.filterBounds(self.geometry)
                    .first()
                    .geometry()
                )
                clipped_data = dataset.obj.collection.map(
                    lambda img: img.clip(country_boundary)
                )
                dataset.obj = hf.Dataset.from_imgcollection(clipped_data)
            if dataset.imagery_type == ImageryType.OPTICAL:
                dataset.obj.apply_func(
                    hf.add_indices,
                    indices=[dataset.algorithm_params["edge_otsu"]["band"]],
                    inplace=True,
                )
            flood_extent = dataset.obj.apply_func(
                hf.edge_otsu, **dataset.algorithm_params["edge_otsu"]
            )

            flood_extents[dataset.name] = flood_extent
        self.flood_extents = flood_extents

    def generate_flood_depths(self):
        pass

    def plot_flood_extents(self, zoom=7, **kwargs):
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
        map = geemap.Map(center=self.centroid, zoom=zoom)
        for ds_name in self.flood_extents:
            for date in self.flood_extents[ds_name].dates:
                img = (
                    self.flood_extents[ds_name].collection.filter(
                        ee.Filter.date(
                            date_parser(date),
                            date_parser(date) + datetime.timedelta(days=1),
                        ),
                    )
                ).mode()

                map.add_layer(
                    img, vis_params=flood_extent_vis_params, name=f"{ds_name} {date}"
                )
        return map

    def plot_flood_depths(self):
        pass


@staticmethod
def _map_data_by_dates(
    datasets: List[hf.Dataset],
    center: list,
    mapping_type: str,
    zoom: int = 7,
) -> geemap.Map:
    Map = geemap.Map(center=center, zoom=zoom)

    for dataset in datasets:
        dates = dataset.obj.dates
        for date in dates:
            img = dataset.obj.collection.filter(ee.Filter.date(date_parser(date)))
            Map.add_layer(
                img,
                vis_params=dataset.visual_params[mapping_type],
                name=f"{dataset.name} {date}",
            )
    return Map


class GFM(Provider):
    def init():
        raise NotImplementedError
