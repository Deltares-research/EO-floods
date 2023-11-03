from EO_Floods.dataset import DATASETS
from EO_Floods.provider import providers, HydraFloods, GFM


class FloodMap:
    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: list,
        datasets: list | str = None,
        provider: providers = providers.HYDRAFLOODS,
    ) -> None:
        self.start_date = start_date
        self.end_date = end_date
        self.geometry = geometry

        if isinstance(datasets, str):
            if datasets not in DATASETS.keys():
                raise ValueError(f"Dataset '{datasets}' not recognized")
            self.datasets = [DATASETS[datasets]]

        elif isinstance(datasets, list):
            self.datasets = [DATASETS[dataset] for dataset in datasets]
        if provider == "hydrafloods":
            self.provider = HydraFloods(
                credentials={},
                datasets=self.datasets,
                start_date=self.start_date,
                end_date=self.end_date,
                geometry=self.geometry,
            )
        elif provider == "GFM":
            self.provider = GFM()
        else:
            raise ValueError(f"Provider '{provider}' not recognized")

    @property
    def info(self):
        return self.provider.info

    def preview_data(self):
        pass

    def generate_flood_extents(self):
        pass


@staticmethod
def _determine_datasets(start_date: str, end_date: str, geometry: list):
    pass


@staticmethod
def _check_space_time_constraints(start_date: str, end_date: str, geometry: list):
    pass
