from enum import Enum
import logging
from typing import List

from EO_Floods.dataset import Dataset, ImageryType, DATASETS
import abc
from abc import ABC

log = logging.getLogger(__name__)


class Providers(Enum):
    HYDRAFLOODS = "hydrafloods"
    GFM = "GFM"


class ProviderBase(ABC):
    def __init__(
        self,
        datasets: List[Dataset],
        start_date: str,
        end_date: str,
        geometry: list,
    ) -> None:
        pass

    @property
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
