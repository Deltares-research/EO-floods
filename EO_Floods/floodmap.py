from typing import List, Optional
import logging
import sys

import geemap.foliumap as geemap

from EO_Floods.providers.hydrafloods.dataset import DATASETS, Dataset
from EO_Floods.utils import get_dates_in_time_range, dates_within_daterange
from EO_Floods.providers import HydraFloods, GFM


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)

PROVIDERS = ["Hydrafloods", "GFM"]


class FloodMap:
    def __init__(
        self,
        start_date: str,
        end_date: str,
        provider: str,
        geometry: List[float],
        datasets: Optional[List[str] | str] = None,
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
        if provider == "GFM":
            self._provider = GFM(
                start_date=start_date, end_date=end_date, geometry=geometry
            )
        elif provider == "Hydrafloods":
            self._provider = HydraFloods(
                datasets=self.datasets,
                start_date=start_date,
                end_date=end_date,
                geometry=geometry,
            )
        else:
            raise ValueError(
                "Provider not given or recognized, choose from [GFM, Hydrafloods]"
            )
        self.provider_name = provider
        log.info(f"Provider set as {provider}")
        log.info("Flood map object initialized")

    @property
    def provider_name(self):
        return self._provider_name

    @provider_name.setter
    def provider_name(self, _provider):
        if _provider not in PROVIDERS:
            raise ValueError(
                f"Given provider '{_provider}' not supported, choose from: {' ,'.join(PROVIDERS)}"
            )
        self._provider_name = _provider

    @property
    def provider(self):
        """Property to fetch the provider object."""
        return self._provider

    def available_data(self):
        """Prints information of the chosen datasets for the given temporal and
        spatial resolution. The information contains the dataset name, the number
        of images, the timestamp of the images, and a quality score in percentage.
        """
        return self.provider.available_data()

    def preview_data(
        self,
        datasets: Optional[List[str] | str] = None,
        dates: Optional[List[str] | str] = None,
        zoom: int = 8,
        vis_params: dict = {},
    ) -> geemap.Map:
        """View data on a geemap instance. This can be used to visually check if
        the quality of the data is sufficient for further processing to flood maps.
        The data can be filtered based on date and dataset name.

        Parameters
        ----------
        datasets : Optional[List[str]  |  str], optional
            A subselection of datasets to display, by default the datasets specified
            for the FloodMap object
        dates : Optional[List[str]  |  str], optional
            A subselection of dates to , by default None
        zoom : int, optional
            zoom level, by default 8
        vis_params : dict, optional
            A dictionary describing the visual parameters for each dataset, by default {}

        Returns
        -------
        geemap.Map
            a geemap.Map instance to visualize in a jupyter notebook
        """
        if self.provider_name == "Hydrafloods":
            if dates:
                dates_within_daterange(
                    dates=dates, start_date=self.start_date, end_date=self.end_date
                )

            if datasets:
                self._provider = HydraFloods(
                    geometry=self.geometry,
                    datasets=_instantiate_datasets(datasets),
                    start_date=self.start_date,
                    end_date=self.end_date,
                )
            return self.provider.view_data(
                zoom=zoom, dates=dates, vis_params=vis_params
            )
        log.warning("GFM does not support previewing data")

    def select_data(
        self,
        dates: Optional[List[str] | str] = None,
        datasets: Optional[List[str]] = None,
    ):
        if dates:
            if isinstance(dates, str):
                dates = [dates]
            dates_within_daterange(
                dates, start_date=self.start_date, end_date=self.end_date
            )

        if self.provider_name == "Hydrafloods":
            self.provider.select_data(datasets=datasets, dates=dates)
        if self.provider_name == "GFM":
            self.provider.select_data(dates=dates)

    def view_flood_extents(self, dates, timeout: int = 300, **kwargs) -> geemap.Map:
        """Plots the generated flood extents on a map together with the data the
        flood extents are generated from.

        timeout: int, optional
            The time in seconds it takes to raise a timeout error

        Returns
        -------
        geemap.Map

        """
        if self.provider_name == "hydrafloods":
            return self.provider.view_flood_extents(timeout=timeout, **kwargs)
        if self.provider_name == "GFM":
            raise NotImplementedError

    def export_data(self, **kwargs):
        if not self._provider:
            raise RuntimeError(
                "FloodMap instance has no data to export, generate flood extents first before calling export_data"
            )
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
