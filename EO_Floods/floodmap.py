from typing import List
import logging
import sys

from EO_Floods.dataset import DATASETS, Dataset
from EO_Floods.provider import providers, HydraFloods, GFM


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)


class FloodMap:
    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: List[float],
        datasets: List[str] | str = None,
        provider: providers = providers.HYDRAFLOODS,
        **kwargs,
    ) -> None:
        self.start_date = start_date
        self.end_date = end_date
        self.geometry = geometry
        self.datasets = _instantiate_datasets(datasets)
        if provider == "hydrafloods":
            self.provider = HydraFloods(
                credentials={},
                datasets=self.datasets,
                start_date=self.start_date,
                end_date=self.end_date,
                geometry=self.geometry,
                **kwargs,
            )
        elif provider == "GFM":
            self.provider = GFM()
        else:
            log.debug(f"Error occured with provider variable: {provider}")
            raise ValueError(f"Provider '{provider}' not recognized")
        log.info("Flood map object initialized")

    @property
    def info(self):
        return self.provider.info

    def preview_data(self, **kwargs):
        return self.provider.preview_data(**kwargs)

    def select_data(
        self,
        datasets: List[str] | str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> List[dict]:
        self.datasets = _instantiate_datasets(datasets)
        return self.provider.select_data(datasets, start_date, end_date)

    def generate_flood_extents(self):
        self.provider.generate_flood_extents()

    def generate_flood_depths(self, **kwargs):
        return self.provider.generate_flood_depths(**kwargs)

    def plot_flood_extents(self, **kwargs):
        return self.provider.plot_flood_extents(**kwargs)


@staticmethod
def _instantiate_datasets(datasets: List[str] | str) -> List[Dataset]:
    if isinstance(datasets, str):
        if datasets not in DATASETS.keys():
            raise ValueError(f"Dataset '{datasets}' not recognized")
        return [DATASETS[datasets]]

    elif isinstance(datasets, list):
        return [DATASETS[dataset] for dataset in datasets]


@staticmethod
def _determine_datasets(start_date: str, end_date: str, geometry: list):
    pass


@staticmethod
def _check_space_time_constraints(start_date: str, end_date: str, geometry: list):
    pass
