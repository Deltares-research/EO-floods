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

    def view_data(self, layer: str = "observed_flood_extent") -> WMS_MapObject:
        return WMS_MapObject(
            start_date=self.start_date,
            end_date=self.end_date,
            layers=layer,
            bbox=self.geometry,
        )

    def generate_flood_extents(self):
        pass

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
