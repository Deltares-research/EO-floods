"""Module containing provider base class."""

import logging
from abc import ABC, abstractmethod
from enum import Enum

log = logging.getLogger(__name__)


class Providers(Enum):
    """Providers enum."""

    HYDRAFLOODS = "hydrafloods"
    GFM = "GFM"


class ProviderBase(ABC):
    """Provider base class."""

    @abstractmethod
    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: list,
    ) -> None:
        """Set up a provider object.

        Parameters
        ----------
        start_date : str
            Start date of the flood event
        end_date : str
            End date of the flood event
        geometry : list
            geometry in a bounding box format [xmin, ymin, xmax. ymax]

        """

