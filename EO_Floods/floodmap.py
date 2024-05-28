from typing import List, Optional
import logging
import sys

import geemap.foliumap as geemap

from EO_Floods.dataset import DATASETS, Dataset
from EO_Floods.utils import get_dates_in_time_range
from EO_Floods.providers import Providers, HydraFloods, GFM


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)


class FloodMap:
    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: List[float],
        datasets: Optional[List[str] | str] = None,
        provider: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Flood map object for creating and exporting flood maps.

        Parameters
        ----------
        start_date : str
            The start date of the time window that you want to search data for.
        end_date : str
            the end date of the time window, end date is exclusive.
        geometry : List[float]
            The region of interest. The region should be a bounding box in the format
            [xmin, ymin, xmax, ymax] and should contain wgs84 coordinates (epsg:4326).
        datasets : List[str] | str, optional
            Name of dataset(s) to use for creating flood maps. The datasets that are
            currently supported are: Sentinel-1, Sentinel-2, Landsat 7, Landsat 8,
            MODIS, and VIIRS. By default None
        provider : providers, optional
            The dataset provider, by default none
        """
        self.start_date = start_date
        self.end_date = end_date
        self.dates = get_dates_in_time_range(
            start_date_str=start_date, end_date_str=end_date
        )
        self.geometry = geometry
        self.datasets = _instantiate_datasets(datasets)
        if provider:
            self.set_provider(provider, datasets)
            log.info(f"Provider set as {provider}")
        log.info("Flood map object initialized")

    def set_provider(self, provider: str, datasets: Optional[List[str] | str]):
        if datasets:
            _instantiate_datasets(datasets)
        if provider == "hydrafloods":
            self.provider = HydraFloods(
                datasets=self.datasets,
                start_date=self.start_date,
                end_date=self.end_date,
                geometry=self.geometry,
            )
        elif provider == "GFM":
            raise NotImplementedError
        else:
            raise ValueError(f"Given provider {provider} not supported")

    def available_data(self) -> List[dict,]:
        """Returns information of the chosen datasets for the given temporal and
        spatial resolution. The information contains the dataset name, the number
        of images, and the timestamp of the images.

        Returns
        -------
        List[dict,]
            List of dictionaries describing the data
        """

        hf = HydraFloods(
            geometry=self.geometry,
            datasets=self.datasets,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        return hf.available_data()

    def preview_data(self, **kwargs) -> geemap.Map:
        """Preview the data in a map.

        Returns
        -------
        geemap.Map
            Map object containing the data specified in the flood map object
        """
        return self.provider.preview_data(**kwargs)

    def select_data(
        self,
        datasets: Optional[List[str] | str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[dict]:
        """Select data for futher processing. Data can be selected based on the
        datasets name and start and end date.

        Parameters
        ----------
        datasets : List[str] | str, optional
            name(s) of the selected dataset(s), by default None
        start_date : str, optional
            start date in YYYY-mm-dd, by default None
        end_date : str, optional
            end date in YYYY-mm-dd, end date is exclusive, by default None

        Returns
        -------
        List[dict]
            description of the selected data in the same format as FloodMap.info
        """
        self.datasets = _instantiate_datasets(datasets)
        return self.provider.select_data(datasets, start_date, end_date)

    def generate_flood_extents(self):
        """Generates flood extents."""
        self.provider.generate_flood_extents()

    def generate_flood_depths(self, **kwargs):
        raise NotImplementedError
        return self.provider.generate_flood_depths(**kwargs)

    def plot_flood_extents(self, timeout: int = 60, **kwargs) -> geemap.Map:
        """Plots the generated flood extents on a map together with the data the
        flood extents are generated from.

        timeout: int, optional
            The time in seconds it takes to raise a timeout error

        Returns
        -------
        geemap.Map

        """
        return self.provider.plot_flood_extents(timeout=timeout, **kwargs)

    def export_data(self, **kwargs):
        return self.provider.export_data(**kwargs)


def _instantiate_datasets(datasets: Optional[List[str] | str]) -> List[Dataset]:
    if isinstance(datasets, str):
        if datasets not in DATASETS.keys():
            raise ValueError(f"Dataset '{datasets}' not recognized")
        return [DATASETS[datasets]]

    elif isinstance(datasets, list):
        return [DATASETS[dataset] for dataset in datasets]
    else:
        return [dataset for dataset in DATASETS.values()]
