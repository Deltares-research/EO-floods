import logging
from typing import List

import requests

from EO_Floods.providers import ProviderBase
from EO_Floods.providers.GFM.auth import BearerAuth, GFM_authenticate
from EO_Floods.providers.GFM.leaflet import WMS_MapObject
from EO_Floods.utils import coords_to_geojson

log = logging.getLogger(__name__)
API_URL = "https://api.gfm.eodc.eu/v2/"


class GFM(ProviderBase):
    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: List[float],
        *,
        email=None,
        pwd=None,
    ):
        self.user: dict = GFM_authenticate(email, pwd)
        self.aoi_id: str = self._create_aoi(geometry=coords_to_geojson(geometry))
        self.start_date: str = start_date
        self.end_date: str = end_date
        self.geometry: List[float] = geometry
        self.products: dict = self._get_products()

    def view_data(self, layer: str = "observed_flood_extent") -> WMS_MapObject:
        return WMS_MapObject(
            start_date=self.start_date,
            end_date=self.end_date,
            layers=layer,
            bbox=self.geometry,
        )

    def available_data(self):
        dates = [product["product_time"] for product in self.products]
        log.info(f"For the following dates there is GFM data: {dates}")

    def select_data(self, dates: List[str]):
        products = [
            product for product in self.products if product["product_time"] in dates
        ]
        if not products:
            raise ValueError(f"No data found for given date(s): {', '.join(dates)}")
        self.products = products

    def export_data(self):
        log.info("Retrieving download link")

        for product in self.products:
            r = requests.get(
                url=API_URL
                + f"download/product/{product['product_id']}/{self.user['client_id']}",
                auth=BearerAuth(self.user["access_token"]),
            )
            if r.status_code != 200:
                r.raise_for_status()
            print(r.json())

    def _create_aoi(self, geometry) -> str:
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
        )

        if r.status_code != 201:
            r.raise_for_status()
        log.info("Successfully uploaded geometry to GFM server")

        return r.json().get("aoi_id")

    def _get_products(self):
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
        )
        if r.status_code != 200:
            r.raise_for_status()
        return r.json()["products"]
