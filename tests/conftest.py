import pytest
from EO_Floods.auth import ee_initialize
from EO_Floods.dataset import DATASETS
from EO_Floods.providers import HydraFloods
from EO_Floods.floodmap import FloodMap

ee_initialize()


def get_hydrafloods_instance(dataset_list: list) -> HydraFloods:
    datasets = [DATASETS[dataset] for dataset in dataset_list]
    return HydraFloods(
        datasets=datasets,
        start_date="2023-04-01",
        end_date="2023-04-30",
        geometry=[4.221067, 51.949474, 4.471006, 52.073727],
    )


@pytest.fixture()
def flood_map() -> FloodMap:
    return FloodMap(
        start_date="2022-10-01",
        end_date="2022-10-15",
        geometry=[67.740187, 27.712453, 68.104933, 28.000935],
    )
