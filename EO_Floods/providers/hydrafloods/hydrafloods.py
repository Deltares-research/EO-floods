"""Hydrafloods provider."""

from __future__ import annotations

import logging
import multiprocessing.pool
import re

import ee
import geemap.foliumap as geemap
import hydrafloods as hf
from hydrafloods.geeutils import batch_export
from tabulate import tabulate

from EO_Floods.providers import ProviderBase
from EO_Floods.providers.hydrafloods.dataset import (
    Dataset,
    HydraFloodsDataset,
    ImageryType,
)
from EO_Floods.utils import (
    coords_to_ee_geom,
    date_parser,
    get_centroid,
)

log = logging.getLogger(__name__)


class HydraFloods(ProviderBase):
    """HydraFloods provider class."""

    def __init__(
        self,
        datasets: list[Dataset],
        start_date: str,
        end_date: str,
        geometry: list[float],
    ) -> None:
        """Instantiate HydraFloods provider class.

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
        self.datasets = [HydraFloodsDataset(dataset, self.geometry, start_date, end_date) for dataset in datasets]

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
            output += f"Dataset ID: {dataset.obj.asset_id}\n"
            output += f"Providers: {', '.join(dataset.providers)}\n\n"

            if n_images > 0:
                dates = dataset.obj.dates
                qa_scores = dataset.quality_score()
                table_list = [[x, y] for x, y in zip(dates, qa_scores)]
                table = tabulate(
                    table_list,
                    headers=["Timestamp", "Quality score (%)"],
                    tablefmt="orgtbl",
                )
                output += table + "\n\n"

        log.info(output)

    def view_data(
        self,
        zoom: int = 8,
        dates: list[str] | str | None = None,
        vis_params: dict | None = None,
    ) -> geemap.Map:
        """View data on a geemap instance.

        This can be used to visually check if
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
        m = geemap.Map(center=self.centroid, zoom=zoom)
        if isinstance(dates, str):
            dates = [dates]
        if vis_params is None:
            vis_params = {}
        for dataset in self.datasets:
            if dates is None:
                dates = dataset.obj.dates
            for date in dates:
                img = _filter_collection_by_dates(date, dataset)
                m.add_layer(
                    img,
                    vis_params=vis_params.get(
                        dataset.name,
                        dataset.visual_params,
                    ),  # If no vis_params are given take the default visual params for the dataset objects
                    name=f"{dataset.name} {date}",
                )
        return m

    def select_data(self, datasets: list[str] | None = None, dates: list[str] | None = None) -> None:
        """Select data for processing.

        Parameters
        ----------
        datasets : list[str] | None, optional
            list of datasets to select data from, by default None
        dates : list[str] | None, optional
            list of dates to select data by, by default None

        """
        if datasets:
            self.datasets = [dataset for dataset in self.datasets if dataset.name in datasets]
        if dates:
            for dataset in self.datasets:
                # Filter the dataset on dates
                f = _multiple_dates_filter(dates) if len(dates) > 1 else _date_filter(dates[0])
                dataset.obj.filter(f, inplace=True)

    def _generate_flood_extents(self, dates: list[str] | None = None, *, clip_ocean: bool = True) -> None:
        """Generate flood extents for the given temporal and spatial resolution.

        Parameters
        ----------
        dates: list of str, optional
            list of date strings for making a subselection of images.
        clip_ocean : bool, optional
            Option for clipping ocean pixels from the images. Ocean pixels can negatively
            influence the edge otsu algorithm. The clipping is done by using country
            borders, so be aware when your region of interest is across country
            boundaries. By default True.

        """
        flood_extents = {}
        for dataset in self.datasets:
            log.info("Generating flood extents for %s dataset", dataset.name)
            if dataset.obj.n_images < 1:
                warn_msg = f"{dataset.name} has no images for date range {self.start_date}/{self.end_date}."
                log.warning(
                    warn_msg,
                )
                continue
            if dates:
                # Filter the dataset on dates
                f = _multiple_dates_filter(dates) if len(dates) > 1 else _date_filter(dates[0])
                dataset.obj.filter(f, inplace=True)

            # Clip
            if clip_ocean:
                log.info("Clipping image to country boundaries")
                country_boundary = (
                    ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0")
                    .filterBounds(self.geometry)
                    .first()
                    .geometry()
                )

                clipped_data = dataset.obj.collection.map(lambda img: img.clip(country_boundary))  # noqa: B023
                dataset.obj = hf.Dataset.from_imgcollection(clipped_data)
            if dataset.imagery_type == ImageryType.OPTICAL:
                log.debug("Calculating MNDWI for %s", dataset.name)
                dataset.obj.apply_func(
                    hf.add_indices,
                    indices=[dataset.algorithm_params["edge_otsu"]["band"]],
                    inplace=True,
                )
                dataset.obj.apply_func(lambda x: x.cast({"mndwi": "double"}), inplace=True)
            log.info("Applying edge-otsu thresholding")
            flood_extent = dataset.obj.apply_func(
                hf.edge_otsu,
                **dataset.algorithm_params["edge_otsu"],
            )

            # Invert values of flood extent so that water=1, land=0
            flood_extent = flood_extent.apply_func(lambda x: x.eq(0).copyProperties(x, ["system:time_start"]))

            flood_extents[dataset.name] = flood_extent
        self.flood_extents = flood_extents

    def generate_flood_depths(self) -> None:
        """Generate flood depths."""
        raise NotImplementedError

    def view_flood_extents(
        self,
        dates: list[str] | None = None,
        zoom: int = 8,
        timeout: int = 60,
        *,
        clip_ocean: bool = False,
    ) -> geemap.Map:
        """View the flood extents on a geemap.Map object.

        Parameters
        ----------
        dates : list, optional
            list of dates to view the data for
        zoom : int, optional
            Zoom level of the map window, by default 8
        timeout: int
            timeout in seconds, this function can take a long time to process all the data
            and can thus be given an timeout.
        clip_ocean: bool
            Images will be clipped by country and ocean borders

        Returns
        -------
        geemap.Map
            Map containing the flood extents and the data the flood extents are
            based on.

        """
        if not hasattr(self, "flood_extents"):
            self._generate_flood_extents(dates=dates, clip_ocean=clip_ocean)

        try:
            with multiprocessing.pool.ThreadPool() as pool:
                return_value = pool.apply_async(self._plot_flood_extents, (zoom,)).get(timeout=timeout)
        except multiprocessing.TimeoutError as exc:
            err_msg = (
                "Plotting flood extents has timed out, increase the time out"
                " threshold or plot a smaller selection of your data"
            )
            raise TimeoutError(err_msg) from exc
        return return_value

    def export_data(  # noqa: PLR0913 D417
        self,
        *,
        export_type: str = "toDrive",
        include_base_data: bool = False,
        folder: str | None = None,
        ee_asset_path: str = "",
        clip_ocean: bool = True,
        dates: list[str] | None = None,
        scale: float | None = None,
        **kwargs: dict,
    ) -> None:
        """Export the generated data to a Google Drive or as Earth Engine asset.

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
        clip_ocean: bool
            Images will be clipped by country and ocean borders
        dates: list
            list of dates to select data with
        scale : int or float, optional
            Scale (resolution) in meters at which the image is exported, by default
            the scale of the flood extent image.

        """
        if export_type == "toDrive":
            folder = "EO_Floods"

        if not hasattr(self, "flood_extents"):
            self._generate_flood_extents(dates, clip_ocean=clip_ocean)
        for ds in self.flood_extents:
            log_msg = f"Exporting {ds} flood extents {export_type[:2]+' '+export_type[2:]}"
            log.info(log_msg)

            if not scale:
                scale = (self.flood_extents[ds].collection.first().select("water").projection().nominalScale(),)
            batch_export(
                collection=self.flood_extents[ds].collection,
                collection_asset=ee_asset_path,
                export_type=export_type,
                folder=folder,
                suffix=f"{ds.replace(' ', '_')}_flood_extent",
                scale=scale,
                **kwargs,
            )

        if include_base_data:
            for dataset in self.datasets:
                log_msg = f"Exporting {dataset.name} {export_type[:2]+' '+export_type[2:]}"
                log.info(log_msg)
                batch_export(
                    collection=dataset.obj.collection,
                    collection_asset=ee_asset_path + f"{dataset.short_name}_EO_Floodmap",
                    export_type=export_type,
                    folder=folder,
                    region=dataset.obj.collection.geometry(),
                    suffix=dataset.short_name,
                    scale=dataset.obj.collection.first().select(1).projection().nominalScale(),
                    **kwargs,
                )

    def _plot_flood_extents(self, zoom: int) -> geemap.Map:
        flood_extent_vis_params = {
            "bands": ["water"],
            "min": 0,
            "max": 1,
            "palette": ["#C0C0C0", "#000080"],
        }
        m = self.view_data(zoom=zoom)
        for ds_name in self.flood_extents:
            img_col = self.flood_extents[ds_name].collection
            n_images = img_col.size().getInfo()
            for n in range(n_images):
                img = ee.Image(img_col.toList(n_images).get(n))
                m.addLayer(
                    img,
                    vis_params=flood_extent_vis_params,
                    name=f"{ds_name}  flood extent",
                )

            max_extent_img = self.flood_extents[ds_name].collection.max()
            m.add_layer(
                max_extent_img,
                vis_params=flood_extent_vis_params,
                name=f"{ds_name} max flood extent",
            )
        return m


def _date_filter(date: str) -> ee.Filter:
    d = ee.Date(date_parser(date))
    # If timestamp contains h:m:s filter on seconds
    if re.findall(r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})", date):
        return ee.Filter.date(d, d.advance(1, "second"))
    # else by day
    return ee.Filter.date(d, d.advance(1, "day"))


def _multiple_dates_filter(dates: list[str]) -> ee.Filter:
    filters = [_date_filter(date) for date in dates]
    return ee.Filter.Or(*filters)


def _filter_collection_by_dates(date: str, dataset: Dataset) -> ee.ImageCollection:
    return dataset.obj.collection.filter(_date_filter(date))
