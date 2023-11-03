import abc
from abc import ABC
from typing import List
from enum import Enum

import hydrafloods as hf

from EO_Floods.dataset import Dataset
from EO_Floods.utils import coords_to_ee_geom


class providers(Enum):
    HYDRAFLOODS = "hydrafloods"
    GFM = "GFM"


class Provider(ABC):
    @abc.abstractmethod
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


class HydraFloods(Provider):
    def __init__(
        self,
        credentials: dict,
        datasets: List[Dataset],
        start_date: str,
        end_date: str,
        geometry: List[float],
    ) -> None:
        self.pre_configured_datasets = datasets
        self.geometry = coords_to_ee_geom(geometry)
        self.start_date = start_date
        self.end_date = end_date

        HF_datasets = {
            "Sentinel-1": hf.Sentinel1,
            "Sentinel-2": hf.Sentinel2,
            "Landsat 7": hf.Landsat7,
            "Landsat 8": hf.Landsat8,
            "VIIRS": hf.Viirs,
            "MODIS": hf.Modis,
        }
        init_datasets = []
        for dataset in datasets:
            init_datasets.append(
                HF_datasets[dataset.name](
                    region=self.geometry,
                    start_time=self.start_date,
                    end_time=self.end_date,
                )
            )
        self.datasets = init_datasets

    @property
    def info(self):
        dataset_info = []
        for dataset in self.datasets:
            dataset_info.append(
                {
                    "Dataset ID": dataset.asset_id,
                    "Number of images": dataset.n_images,
                    "Dates": dataset.dates,
                }
            )
        return dataset_info

    def preview_data(self):
        pass

    def generate_flood_extents(self):
        pass

    def generate_flood_depths(self):
        pass


class GFM(Provider):
    def init():
        raise NotImplementedError
