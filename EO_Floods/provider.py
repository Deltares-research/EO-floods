import abc
from abc import ABC


class Provider(ABC):
    @abc.abstractmethod
    def __init__(self, credentials) -> None:
        pass

    @abc.abstractmethod
    def preview_data(self):
        pass

    @abc.abstractmethod
    def generate_flood_extents(self):
        pass

    @abc.abstractmethod
    def generate_flood_depths(self):
        pass
