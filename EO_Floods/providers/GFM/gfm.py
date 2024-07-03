import logging
from typing import List

from EO_Floods.providers import ProviderBase
from EO_Floods.providers.GFM.auth import GFM_authenticate
from EO_Floods.utils import coords_to_geojson
from EO_Floods.providers.GFM.leaflet import WMS_MapObject

logger = logging.getLogger(__name__)


class GFM(ProviderBase):
    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: List[float],
    ):
        self.user: dict = GFM_authenticate()
        self.geojson: dict = coords_to_geojson(geometry)
        self.start_date: str = start_date
        self.end_date: str = end_date
        self.geometry: List[float] = geometry

    def preview_data(self, layer: str = "observed_flood_extent") -> WMS_MapObject:
        return WMS_MapObject(
            start_date=self.start_date,
            end_date=self.end_date,
            layers=layer,
            bbox=self.geometry,
        )
