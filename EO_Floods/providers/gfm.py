import logging
from typing import List

from EO_Floods.providers import ProviderBase
from EO_Floods.auth import GFM_authenticate
from EO_Floods.utils import coords_to_geojson

logger = logging.getLogger(__name__)


class GFM(ProviderBase):
    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: List[float],
    ):
        self.user: dict = GFM_authenticate()
        self.geometry: dict = coords_to_geojson(geometry)
        self.start_date = start_date
        self.end_date = end_date
