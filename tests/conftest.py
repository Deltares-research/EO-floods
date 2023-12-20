from EO_Floods.auth import ee_initialize
from EO_Floods.dataset import DATASETS
from EO_Floods.provider import HydraFloods

ee_initialize()


def get_hydrafloods_instance(dataset_list: list) -> HydraFloods:
    datasets = [DATASETS[dataset] for dataset in dataset_list]
    return HydraFloods(
        datasets=datasets,
        start_date="2023-04-01",
        end_date="2023-04-30",
        geometry=[4.221067, 51.949474, 4.471006, 52.073727],
    )
