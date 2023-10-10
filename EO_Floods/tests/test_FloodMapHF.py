from EO_Floods.floodmap_hf import FloodMapHF

import hydrafloods as hf
import ee
import geemap.foliumap as geemap


def test_init(hf_floodmap_S1):
    geometry_coordinates = [4.2088, 51.9182, 4.6636, 52.1683]
    start_date = "2023-04-01"
    end_date = "2023-04-30"

    floodmap = hf_floodmap_S1
    assert isinstance(floodmap.dataset, hf.datasets.Sentinel1)
    imgcollection = ee.ImageCollection("COPERNICUS/S1_GRD")

    floodmap = FloodMapHF(
        geometry=geometry_coordinates,
        start_date=start_date,
        end_date=end_date,
        dataset=imgcollection,
    )
    assert isinstance(floodmap.dataset, hf.Dataset)
    assert floodmap.dataset.asset_id == "COPERNICUS/S1_GRD"


def test_info(hf_floodmap_S1):
    dataset_info = hf_floodmap_S1.info
    assert dataset_info["n_images"] == 10
    assert dataset_info["dataset_id"] == "COPERNICUS/S1_GRD"


def test_preview_data(hf_floodmap_S1):
    map = hf_floodmap_S1.preview_data(zoom=5)
    assert isinstance(map, geemap.Map)
    assert map.options["zoom"] == 5
    map = hf_floodmap_S1.preview_data(dates=[hf_floodmap_S1.dataset.dates[0]])
    assert (
        map._children[list(map._children.keys())[-1]].layer_name
        == hf_floodmap_S1.dataset.dates[0]
    )
