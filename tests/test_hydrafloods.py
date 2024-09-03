from mock import patch
import hydrafloods as hf
import ee
import geemap
import pytest
from EO_Floods.providers.hydrafloods import HydraFloodsDataset, HydraFloods
from EO_Floods.providers.hydrafloods.dataset import DATASETS


def hydrafloods_instance(dataset_list: list) -> HydraFloods:
    datasets = [DATASETS[dataset] for dataset in dataset_list]
    return HydraFloods(
        datasets=datasets,
        start_date="2022-10-01",
        end_date="2022-10-15",
        geometry=[67.740187, 27.712453, 68.104933, 28.000935],
    )


def test_Hydrafloods_init():
    hydrafloods_provider = hydrafloods_instance(["Sentinel-1", "Sentinel-2"])
    assert isinstance(hydrafloods_provider.datasets[0], HydraFloodsDataset)
    assert isinstance(hydrafloods_provider.datasets[0].obj, hf.Sentinel1)
    assert isinstance(hydrafloods_provider.geometry, ee.geometry.Geometry)


def test_generate_flood_extents():
    hf_provider = hydrafloods_instance(["Sentinel-1"])
    dates = ["2022-10-05 01:25:51.000", "2022-10-05 01:25:26.000"]
    hf_provider.generate_flood_extents(dates=dates)


def test_view_flood_extents():
    hf_provider = hydrafloods_instance(["Sentinel-1"])
    with pytest.raises(
        RuntimeError,
        match=r"generate_flood_extents\(\) needs to be called before calling this method",
    ):
        hf_provider.view_flood_extents()
    hf_provider.generate_flood_extents(
        dates=[
            "2022-10-05 01:25:51.000",
        ]
    )
    flood_map = hf_provider.view_flood_extents()
    assert isinstance(flood_map, geemap.foliumap.Map)
    with pytest.raises(
        TimeoutError,
        match="Plotting flood extents has timed out, increase the time out threshold or plot a smaller selection of your data",
    ):
        hf_provider.view_flood_extents(timeout=1)


def test_export_data():
    hf_provider = hydrafloods_instance(["Landsat 8"])
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
