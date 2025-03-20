"""Global Flood Monitor Provider class."""

from __future__ import annotations

import logging

import requests

from eo_floods.providers import ProviderBase
from eo_floods.providers.GFM.auth import BearerAuth, authenticate_gfm
from eo_floods.providers.GFM.leaflet import WMSMap
from eo_floods.utils import coords_to_geojson

log = logging.getLogger(__name__)
API_URL = "https://api.gfm.eodc.eu/v2/"


class GFM(ProviderBase):
    """Provider class for retrieving and processing GFM data."""

    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: list[float],
        *,
        email: str | None = None,
        pwd: str | None = None,
    ) -> None:
        """Instantiate a GFM provider object.

        Parameters
        ----------
        start_date : str
            start date of the period to retrieve flood data for
        end_date : str
            end date  of the period to retrieve flood data for
        geometry : list[float]
            bounding box in [xmin, ymin, xmax, ymax] format
        email : _type_, optional
            email of the GFM user account, by default None
        pwd : _type_, optional
            password of the GFM user account, by default None

        """
        self.user: dict = authenticate_gfm(email, pwd)
        self.aoi_id: str = self._create_aoi(geometry=coords_to_geojson(geometry))
        self.start_date: str = start_date
        self.end_date: str = end_date
        self.geometry: list[float] = geometry
        self.products: dict = self._get_products()

    def view_data(self, layer: str = "observed_flood_extent") -> WMSMap:
        """View the data for the given period and geometry.

        Parameters
        ----------
        layer : str, optional
            name of the data layer, by default "observed_flood_extent"

        Returns
        -------
        WMS_Map
            a ipyleaflet map object wrapped in a custom map class.

        """
        wms_map = WMSMap(
            start_date=self.start_date,
            end_date=self.end_date,
            layers=layer,
            bbox=self.geometry,
        )
        return wms_map.get_map()

    def available_data(self) -> None:
        """Show the available data for the given time period and geometry."""
        dates = [product["product_time"] for product in self.products]
        log.info("For the following dates there is GFM data: %s", dates)

    def select_data(self, dates: list[str]) -> None:
        """Select data by supplying a list of timestamps.

        Parameters
        ----------
        dates : list[str]
            a list of timestamps that should match at least one of the timestamps given with
                the available_data method

        """
        if not isinstance(dates, list):
            err_msg = f"dates should be a list of dates, not {type(dates)}"
            raise TypeError(err_msg)
        products = [product for product in self.products if product["product_time"] in dates]
        if not products:
            err_msg = f"No data found for given date(s): {', '.join(dates)}"
            raise ValueError(err_msg)
        self.products = products

    def export_data(self) -> None:
        """Retrieve a download link for downloading the GFM data."""
        log.info("Retrieving download link")

        for product in self.products:
            r = requests.get(
                url=API_URL + f"download/product/{product['product_id']}/{self.user['client_id']}",
                auth=BearerAuth(self.user["access_token"]),
                timeout=300,
            )
            if r.status_code != 200:  # noqa: PLR2004
                r.raise_for_status()
            link = r.json()
            log.info("Image: %s, download link: %s", product["product_time"], link)

    def _create_aoi(self, geometry: list[float]) -> str:
        log.info("Uploading geometry to GFM server")
        payload = {
            "aoi_name": "flood_aoi",
            "user_id": self.user["client_id"],
            "description": "area of interest for flood mapping",
            "geoJSON": geometry,
        }

        r = requests.post(
            API_URL + "/aoi/create",
            json=payload,
            auth=BearerAuth(self.user["access_token"]),
            timeout=120,
        )

        if r.status_code != 201:  # noqa: PLR2004
            r.raise_for_status()
        log.info("Successfully uploaded geometry to GFM server")

        return r.json().get("aoi_id")

    def _get_products(self) -> dict:
        log.info("Retrieving GFM product information")
        params = {
            "time": "range",
            "from": self.start_date + "T00:00:00",
            "to": self.end_date + "T23:59:59",
        }
        r = requests.get(
            API_URL + f"/aoi/{self.aoi_id}/products",
            auth=BearerAuth(self.user["access_token"]),
            params=params,
            timeout=120,
        )
        if r.status_code != 200:  # noqa: PLR2004
            r.raise_for_status()
        return r.json()["products"]
