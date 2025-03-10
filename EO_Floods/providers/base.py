import logging
from abc import ABC
from enum import Enum

log = logging.getLogger(__name__)


class Providers(Enum):
    HYDRAFLOODS = "hydrafloods"
    GFM = "GFM"


class ProviderBase(ABC):
    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: list,
    ) -> None:
        pass
