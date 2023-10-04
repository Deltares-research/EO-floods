from EO_Floods.floodmap_hf import FloodMapHF

import hydrafloods as hf
import ee


def test_init():
    geometry_coordinates = [4.2088, 51.9182, 4.6636, 52.1683]
    start_date = "2023-04-01"
    end_date = "2023-04-30"
    dataset = "Sentinel 1"

    floodmap = FloodMapHF(
        geometry=geometry_coordinates,
        start_date=start_date,
        end_date=end_date,
        dataset=dataset,
    )
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


def test_dataset_preview():
    geometry_coordinates = [4.2088, 51.9182, 4.6636, 52.1683]
    start_date = "2023-04-01"
    end_date = "2023-04-30"
    dataset = "Sentinel 1"

    floodmap = FloodMapHF(
        geometry=geometry_coordinates,
        start_date=start_date,
        end_date=end_date,
        dataset=dataset,
    )
    data_preview = floodmap.data_preview
    assert data_preview["n_images"] == 10
    assert data_preview["dataset_id"] == "COPERNICUS/S1_GRD"
