import pytest
import geemap.foliumap as geemap
import logging
import hydrafloods as hf
import re
from EO_Floods.floodmap import FloodMap, _instantiate_datasets
from EO_Floods.providers.hydrafloods.dataset import Dataset, Sentinel1, VIIRS, DATASETS
from EO_Floods.providers.hydrafloods import HydraFloods


def test_init():
    floodmap = FloodMap(
        start_date="2023-04-01",
        end_date="2023-04-30",
        geometry=[4.221067, 51.949474, 4.471006, 52.073727],
        datasets=["Sentinel-1", "Landsat 8"],
        provider="Hydrafloods",
    )
    assert isinstance(floodmap, FloodMap)
    assert isinstance(floodmap.datasets[0], Dataset)
    assert floodmap.datasets[0].name == "Sentinel-1"
    assert floodmap.datasets[1].name == "Landsat 8"

    with pytest.raises(ValueError, match=r"Dataset 'sentinel' not recognized"):
        floodmap = FloodMap(
            start_date="2023-04-01",
            end_date="2023-04-30",
            geometry=[4.221067, 51.949474, 4.471006, 52.073727],
            datasets="sentinel",
            provider="Hydrafloods",
        )
    with pytest.raises(ValueError, match=re.escape(r"Provider not given or recognized, choose from [GFM, Hydrafloods]")):
        floodmap = FloodMap(
            start_date="2023-04-01",
            end_date="2023-04-30",
            geometry=[4.221067, 51.949474, 4.471006, 52.073727],
            datasets=["Sentinel-1", "Landsat 8"],
            provider="copernicus",
        )



def test_available_data(caplog, flood_map):
    caplog.set_level(logging.INFO)
    flood_map.available_data()
    assert "Sentinel-1" in caplog.text
    assert "Sentinel-2" in caplog.text
    assert "Landsat 7" in caplog.text
    assert "Landsat 8" in caplog.text
    assert "VIIRS" in caplog.text
    assert "MODIS" in caplog.text


def test_preview_data(flood_map):
    viewer = flood_map.preview_data(
        datasets=["Sentinel-1"],
        dates=["2022-10-05 01:25:51.000", "2022-10-05 01:25:26.000"],
    )
    assert isinstance(viewer, geemap.foliumap.Map)
    # assert that there are two ee tile layers in the map object
    for key in list(viewer._children.keys())[-2:]:
        assert isinstance(
            viewer._children[key], geemap.ee_tile_layers.EEFoliumTileLayer
        )


@pytest.mark.integration()
def test_workflow(caplog, mocker):
    floodmap = FloodMap(
        start_date="2023-04-01",
        end_date="2023-04-30",
        geometry=[4.221067, 51.949474, 4.471006, 52.073727],
        datasets="Landsat 8",
        provider="Hydrafloods",
    )
    floodmap.available_data()
    preview = floodmap.preview_data()
    assert isinstance(preview, geemap.Map)
    data_view = floodmap.view_flood_extents()
    assert isinstance(data_view, geemap.Map)
    assert hasattr(floodmap.provider, "flood_extents")
    mock_batch_export = mocker.patch("EO_Floods.providers.hydrafloods.hydrafloods.batch_export")
    floodmap.export_data()
    mock_batch_export.assert_called()


def test_instantiate_datasets():
    datasets = _instantiate_datasets(datasets=["Sentinel-1", "VIIRS"])
    assert isinstance(datasets, list)
    assert len(datasets) == 2
    assert isinstance(datasets[0], Sentinel1)
    assert isinstance(datasets[1], VIIRS)

    dataset = _instantiate_datasets(datasets="Sentinel-1")
    assert len(dataset) == 1
    assert isinstance(dataset, list)
    assert isinstance(dataset[0], Sentinel1)

    err_msg = f"Dataset 'fakedataset' not recognized. Supported datasets are: {','.join(list(DATASETS.keys()))}"
    with pytest.raises(ValueError, match=err_msg):
        _instantiate_datasets(datasets=["fakedataset"])
