import abc
from abc import ABC
from datetime import datetime


class FloodMap(ABC):
    @abc.abstractmethod
    def __init__(
        self, geometry, start_date: datetime, end_date: datetime, dataset: str
    ) -> None:
        pass

    @abc.abstractmethod
    def generate_flood_extents(self):
        pass

    @abc.abstractmethod
    def plot_flood_extents(self):
        pass

    @abc.abstractmethod
    def flood_depths(self):
        pass

    @abc.abstractmethod
    def preview_data(self):
        pass

    @abc.abstractmethod
    def maximum_extent(self):
        pass

    @abc.abstractmethod
    def maximum_duration(self):
        pass

    @abc.abstractmethod
    def maximum_depth(self):
        pass

    @abc.abstractmethod
    def metrics(self):
        pass

    @abc.abstractmethod
    def export_data(self):
        pass
