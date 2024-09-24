"""General API for flood maps in EO-Floods."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

from EO_Floods.providers import GFM, HydraFloods
from EO_Floods.providers.hydrafloods.dataset import DATASETS, Dataset
from EO_Floods.utils import dates_within_daterange, get_dates_in_time_range

if TYPE_CHECKING:
    import geemap.foliumap as geemap
    import ipyleaflet

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)

PROVIDERS = ["Hydrafloods", "GFM"]


class FloodMap:
    """General API for flood maps in EO-Floods."""

    def __init__(
        self,
        start_date: str,
        end_date: str,
        provider: str,
        geometry: list[float],
        datasets: list[str] | str | None = None,
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
            start_date_str=start_date,
            end_date_str=end_date,
        )
        self.geometry = geometry
        self.datasets = _instantiate_datasets(datasets)
        if provider == "GFM":
            self._provider = GFM(
                start_date=start_date,
                end_date=end_date,
                geometry=geometry,
            )
        elif provider == "Hydrafloods":
            self._provider = HydraFloods(
                datasets=self.datasets,
                start_date=start_date,
                end_date=end_date,
                geometry=geometry,
            )
        else:
            err_msg = "Provider not given or recognized, choose from [GFM, Hydrafloods]"
            raise ValueError(err_msg)
        self.provider_name = provider
        log.info("Provider set as %s", provider)
        log.info("Flood map object initialized")

    @property
    def provider_name(self) -> str:
        """Returns name of the provider."""
        return self._provider_name

    @provider_name.setter
    def provider_name(self, _provider: str) -> None:
        if _provider not in PROVIDERS:
            err_msg = f"Given provider '{_provider}' not supported, choose from: {' ,'.join(PROVIDERS)}"
            raise ValueError(err_msg)
        self._provider_name = _provider

    @property
    def provider(self) -> GFM | HydraFloods:
        """Property to fetch the provider object."""
        return self._provider

    def available_data(self) -> None:
        """Print information of the selected datasets.

        The information contains the dataset name, the number
        of images, the timestamp of the images, and a quality score in percentage of the selected datasets.
        """
        self.provider.available_data()

    def preview_data(
        self,
        datasets: list[str] | str | None = None,
        dates: list[str] | str | None = None,
        zoom: int = 8,
        **kwargs: dict[str, Any],
    ) -> geemap.Map | None:
        """View data on a geemap instance.

        This can be used to visually check if the quality of the data is sufficient for further processing to
        flood maps. The data can be filtered based on date and dataset name.

        Parameters
        ----------
        datasets : Optional[List[str]  |  str], optional
            A subselection of datasets to display, by default the datasets specified
            for the FloodMap object
        dates : Optional[List[str]  |  str], optional
            A subselection of dates to , by default None
        zoom : int, optional
            zoom level, by default 8
        kwargs: dict,
            keyword arguments passed to the hydrafloods preview data method.

        Returns
        -------
        geemap.Map
            a geemap.Map instance to visualize in a jupyter notebook

        """
        if self.provider_name == "Hydrafloods":
            if dates:
                dates_within_daterange(
                    dates=dates,
                    start_date=self.start_date,
                    end_date=self.end_date,
                )

            if datasets:
                self._provider = HydraFloods(
                    geometry=self.geometry,
                    datasets=_instantiate_datasets(datasets),
                    start_date=self.start_date,
                    end_date=self.end_date,
                )
            return self.provider.view_data(
                zoom=zoom,
                dates=dates,
                **kwargs,
            )
        log.warning("GFM does not support previewing data")
        return None

    def select_data(
        self,
        dates: list[str] | str | None = None,
        datasets: list[str] | None = None,
    ) -> None:
        """Select data and datasets from the available datasets based on the timestamp of the data.

        Parameters
        ----------
        dates : list[str] | str | None, optional
            the dates to select, by default None
        datasets : list[str] | None, optional
            The datasets to select. Only applicable for the hydrafloods provider, by default None

        """
        if dates:
            if isinstance(dates, str):
                dates = [dates]
            dates_within_daterange(
                dates,
                start_date=self.start_date,
                end_date=self.end_date,
            )

        if self.provider_name == "Hydrafloods":
            self.provider.select_data(datasets=datasets, dates=dates)
        if self.provider_name == "GFM":
            self.provider.select_data(dates=dates)

    def view_flood_extents(self, timeout: int = 300, **kwargs: dict[Any]) -> geemap.Map | ipyleaflet.Map:
        """Plot the generated flood extents on a map.

        Parameters
        ----------
        timeout: int, optional
            The time in seconds it takes to raise a timeout error
        kwargs: dict[Any]
            keyword arguments that are passed to the view_flood_extents HydraFloods method.

        Returns
        -------
        geemap.Map or ipyleaflet.Map

        """
        if self.provider_name == "Hydrafloods":
            return self.provider.view_flood_extents(timeout=timeout, **kwargs)
        if self.provider_name == "GFM":
            return self.provider.view_data()
        return None

    def export_data(self, **kwargs: dict) -> None:
        """Export the flood data."""
        return self.provider.export_data(**kwargs)


def _instantiate_datasets(datasets: list[str] | str) -> list[Dataset]:
    if isinstance(datasets, str):
        if datasets not in DATASETS:
            _dataset_error(dataset_name=datasets)
        return [DATASETS[datasets]]

    if isinstance(datasets, list):
        for dataset in datasets:
            if dataset not in DATASETS:
                _dataset_error(dataset_name=dataset)
        return [DATASETS[dataset] for dataset in datasets]
    return list(DATASETS.values())


def _dataset_error(dataset_name: str) -> None:
    err_msg = f"Dataset '{dataset_name}' not recognized. Supported datasets are: {','.join(list(DATASETS.keys()))}"
    raise ValueError(err_msg)
