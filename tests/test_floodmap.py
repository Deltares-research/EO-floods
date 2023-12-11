import pytest
import geemap.foliumap as geemap
import hydrafloods as hf

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
    with pytest.raises(ValueError, match=r"Provider 'copernicus' not recognized"):
        floodmap = FloodMap(
            start_date="2023-04-01",
            end_date="2023-04-30",
            geometry=[4.221067, 51.949474, 4.471006, 52.073727],
            datasets=["Sentinel-1", "Landsat 8"],
            provider="copernicus",
        )


def test_FloodMap_info():
    floodmap = FloodMap(
        start_date="2023-04-01",
        end_date="2023-04-30",
        geometry=[4.221067, 51.949474, 4.471006, 52.073727],
        datasets="Sentinel-2",
        provider="hydrafloods",
        use_qa=False,
    )

    floodmap_info = floodmap.info
    assert isinstance(floodmap_info, list)
    assert isinstance(floodmap_info[0], dict)
    assert floodmap_info[0]["Number of images"] == 10


def test_FloodMap_preview_data():
    floodmap = FloodMap(
        start_date="2023-04-01",
        end_date="2023-04-30",
        geometry=[4.221067, 51.949474, 4.471006, 52.073727],
        datasets="Sentinel-2",
        provider="hydrafloods",
    )
    map = floodmap.preview_data()
    assert isinstance(map, geemap.Map)


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
