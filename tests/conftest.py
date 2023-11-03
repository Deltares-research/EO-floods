import pytest

from EO_Floods.dataset import DATASETS
from EO_Floods.provider import HydraFloods


@pytest.fixture
def hydrafloods_provider_S1():
    return HydraFloods(
        credentials={},
        datasets=[DATASETS["Sentinel-1"]],
        start_date="2023-04-01",
        end_date="2023-04-30",
        geometry=[4.2088, 51.9182, 4.6636, 52.1683],
    )
