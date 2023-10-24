import abc
from abc import ABC


class Dataset(ABC):
    @abc.abstractmethod
    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: list,
        visParams: dict = None,
        flood_extent_algorithm: str = None,
        flood_depth_algorithm: str = None,
    ):
        pass

    @abc.abstractproperty
    def provider(self):
        pass

    @abc.abstractproperty
    def default_flood_extent_algorithm(self):
        pass

    @abc.abstractproperty
    def algorithm_params(self):
        pass
