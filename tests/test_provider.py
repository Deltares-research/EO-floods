import hydrafloods as hf
import ee

from EO_Floods.provider import HydraFloods
from EO_Floods.dataset import DATASETS


def test_Hydrafloods_init(hydrafloods_provider_S1):
    assert isinstance(hydrafloods_provider_S1.datasets[0], hf.Sentinel1)
    assert isinstance(hydrafloods_provider_S1.geometry, ee.geometry.Geometry)


def test_Hydrafloods_info(hydrafloods_provider_S1):
    data_info = hydrafloods_provider_S1.info
    assert isinstance(data_info, list)
