import logging
from typing import List
import requests

from EO_Floods.providers import ProviderBase
from EO_Floods.providers.GFM.auth import GFM_authenticate
from EO_Floods.utils import coords_to_geojson
from EO_Floods.providers.GFM.leaflet import WMS_MapObject

log = logging.getLogger(__name__)
API_URL = "https://api.gfm.eodc.eu/v2/"


class GFM(ProviderBase):
    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: List[float],
    ):
        self.user: dict = GFM_authenticate()
        print(self.user)
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
        payload = {
            "aoi_name": "flood_aoi",
            "description": "area of interest for flood mapping",
            "user_id": self.user["client_id"],
            "geoJSON": geometry,
        }
        header = {"Authorization": f"Bearer {self.user['access_token']}"}
        r = requests.post(API_URL + "aoi/create", data=payload, headers=header)
        if r.status_code != 201:
            r.raise_for_status()
        log.info("Successfully uploaded geometry to GFM server")
        return r.json().get("aoi_id")
