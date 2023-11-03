import hydrafloods as hf
import ee

from tests.conftest import get_hydrafloods_instance


def test_Hydrafloods_init():
    hydrafloods_provider = get_hydrafloods_instance(["Sentinel-1", "Sentinel-2"])
    assert isinstance(hydrafloods_provider.datasets[0], dict)
    assert isinstance(hydrafloods_provider.datasets[0]["hf_object"], hf.Sentinel1)
    assert isinstance(hydrafloods_provider.geometry, ee.geometry.Geometry)


def test_Hydrafloods_info():
    hydrafloods_provider = get_hydrafloods_instance(["Sentinel-1"])
    data_info = hydrafloods_provider.info
    assert isinstance(data_info, list)
    expected_keys = ["Dataset ID", "Number of images", "Dates"]
    actual_keys = list(data_info[0].keys())
    assert all([a == b for a, b in zip(expected_keys, actual_keys)])
    assert data_info[0]["Dataset ID"] == "COPERNICUS/S1_GRD"
    assert data_info[0]["Number of images"] == 10
