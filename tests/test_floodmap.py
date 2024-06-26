import pytest
import geemap
import hydrafloods as hf
from unittest.mock import patch

from EO_Floods.floodmap import FloodMap
from EO_Floods.dataset import Dataset


def test_FloodMap_init():
    floodmap = FloodMap(
        start_date="2023-04-01",
        end_date="2023-04-30",
        geometry=[4.221067, 51.949474, 4.471006, 52.073727],
        datasets=["Sentinel-1", "Landsat 8"],
        provider="hydrafloods",
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
            provider="hydrafloods",
        )
    with pytest.raises(ValueError, match=r"Given provider 'copernicus' not supported"):
        floodmap = FloodMap(
            start_date="2023-04-01",
            end_date="2023-04-30",
            geometry=[4.221067, 51.949474, 4.471006, 52.073727],
            datasets=["Sentinel-1", "Landsat 8"],
            provider="copernicus",
        )


@patch("builtins.print")
def test_available_data(mocked_print, flood_map):
    flood_map.available_data()
    print_args = mocked_print.mock_calls[0][1][0]
    assert "Sentinel-1" in print_args
    assert "Sentinel-2" in print_args
    assert "Landsat 7" in print_args
    assert "Landsat 8" in print_args
    assert "VIIRS" in print_args
    assert "MODIS" in print_args


def test_view_data(flood_map):
    map = flood_map.view_data(
        datasets=["Sentinel-1"],
        dates=["2022-10-05 01:25:51.000", "2022-10-05 01:25:26.000"],
    )
    assert isinstance(map, geemap.foliumap.Map)
    # assert that there are two ee tile layers in the map object
    for key in list(map._children.keys())[-2:]:
        assert isinstance(map._children[key], geemap.ee_tile_layers.EEFoliumTileLayer)


def test_FloodMap_workflow():
    floodmap = FloodMap(
        start_date="2023-04-01",
        end_date="2023-04-30",
        geometry=[4.221067, 51.949474, 4.471006, 52.073727],
        datasets="Landsat 8",
        provider="hydrafloods",
    )
    info = floodmap.info
    assert isinstance(info, list)
    preview = floodmap.preview_data()
    assert isinstance(preview, geemap.Map)
    data_selection = floodmap.select_data(
        datasets="Landsat 8", start_date="2023-04-03", end_date="2023-04-04"
    )
    assert isinstance(data_selection, list)
    floodmap.generate_flood_extents()
    assert hasattr(floodmap.provider, "flood_extents")
    assert isinstance(floodmap.provider.flood_extents["Landsat 8"], hf.Dataset)
