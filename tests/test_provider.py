from mock import patch
import hydrafloods as hf
import ee
import geemap.foliumap as geemap
import pytest
from EO_Floods.provider import HydraFloodsDataset
from EO_Floods.utils import date_parser
from tests.conftest import get_hydrafloods_instance


def test_Hydrafloods_init():
    hydrafloods_provider = get_hydrafloods_instance(["Sentinel-1", "Sentinel-2"])
    assert isinstance(hydrafloods_provider.datasets[0], HydraFloodsDataset)
    assert isinstance(hydrafloods_provider.datasets[0].obj, hf.Sentinel1)
    assert isinstance(hydrafloods_provider.geometry, ee.geometry.Geometry)


def test_Hydrafloods_info():
    hydrafloods_provider = get_hydrafloods_instance(["Sentinel-1"])
    data_info = hydrafloods_provider.info
    assert isinstance(data_info, list)
    expected_keys = ["Name", "Dataset ID", "Number of images", "Dates"]
    actual_keys = list(data_info[0].keys())
    assert all([a == b for a, b in zip(expected_keys, actual_keys)])
    assert data_info[0]["Dataset ID"] == "COPERNICUS/S1_GRD"
    assert data_info[0]["Number of images"] == 10


def test_preview_data():
    hydrafloods_provider = get_hydrafloods_instance(["Sentinel-1", "Sentinel-2"])
    map = hydrafloods_provider.preview_data()
    assert isinstance(map, geemap.Map)


def test_select_data():
    hydrafloods_provider = get_hydrafloods_instance(
        ["Sentinel-1", "Sentinel-2", "Landsat 8"]
    )
    datasets = "Sentinel-1"
    hydrafloods_provider_info = hydrafloods_provider.select_data(datasets)
    assert isinstance(hydrafloods_provider_info, list)
    assert len(hydrafloods_provider_info) == 1
    assert hydrafloods_provider_info[0]["Name"] == "Sentinel-1"
    assert len(hydrafloods_provider.datasets) == 1

    hydrafloods_provider_2 = get_hydrafloods_instance(["Sentinel-1", "Sentinel-2"])
    start_date = str(date_parser(hydrafloods_provider.datasets[0].obj.dates[0]).date())
    end_date = str(date_parser(hydrafloods_provider.datasets[0].obj.dates[4]).date())
    hydrafloods_provider_info = hydrafloods_provider_2.select_data(
        datasets="Sentinel-1", start_date=start_date, end_date=end_date
    )
    assert isinstance(hydrafloods_provider_info, list)
    dates = hydrafloods_provider_info[0]["Dates"]
    start_date = date_parser(start_date)
    end_date = date_parser(end_date)
    for date in dates:
        assert start_date <= date_parser(date) <= end_date


def test_generate_flood_extents():
    hf_provider = get_hydrafloods_instance(["Sentinel-2"])
    with pytest.warns(
        UserWarning,
        match=r"Sentinel-2 has no images for date range 2023-04-01 - 2023-04-30.",
    ):
        hf_provider.generate_flood_extents()

    hf_provider = get_hydrafloods_instance(["Landsat 8"])
    hf_provider.generate_flood_extents()
    assert "Landsat 8" in hf_provider.flood_extents.keys()
    assert isinstance(hf_provider.flood_extents["Landsat 8"], hf.Dataset)


def test_plot_flood_extents():
    hf_provider = get_hydrafloods_instance(["Sentinel-1"])
    with pytest.raises(
        RuntimeError,
        match=r"generate_flood_extents\(\) needs to be called before calling this method",
    ):
        hf_provider.plot_flood_extents()


def test_export_data():
    hf_provider = get_hydrafloods_instance(["Landsat 8"])
    with pytest.raises(
        RuntimeError,
        match=r"First call generate_flood_extents\(\) before calling export_data\(\)",
    ):
        hf_provider.export_data()

    @patch("EO_Floods.provider.batch_export")
    def test_batch_export_call(mock_batch_export):
        hf_provider.generate_flood_extents()
        hf_provider.export_data()
        assert mock_batch_export.call_count == 1
        hf_provider.export_data(include_base_data=True, scale=1000)
        assert mock_batch_export.call_count == 3

    test_batch_export_call()
