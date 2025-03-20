from mock import patch
import hydrafloods as hf
import ee

import geemap.foliumap as geemap
import pytest
import logging
from eo_floods.providers.hydrafloods import HydraFloodsDataset, HydraFloods
from eo_floods.providers.hydrafloods.dataset import DATASETS


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


def test_available_data(caplog):
    caplog.set_level(logging.INFO)
    hf_provider = hydrafloods_instance(["Sentinel-1", "Landsat 7"])
    hf_provider.available_data()
    assert "Sentinel-1" in caplog.text
    assert "Landsat 7" in caplog.text
    assert "Quality score" in caplog.text
    assert "GFM, Hydrafloods" in caplog.text


def test_view_data():
    hydrafloods_provider = hydrafloods_instance(["Sentinel-1"])
    m = hydrafloods_provider.view_data()
    assert isinstance(m, geemap.Map)



def test_select_data():
    hf_provider = hydrafloods_instance(["Sentinel-1", "Landsat 7"])
    hf_provider.select_data(datasets=["Sentinel-1"])
    assert len(hf_provider.datasets) == 1
    assert hf_provider.datasets[0].name == "Sentinel-1"
    dates = ["2022-10-05 01:25:51.000", "2022-10-05 01:25:26.000"]
    hf_provider.select_data(dates=dates)

    assert all([date in dates for date in hf_provider.datasets[0].obj.dates])

     

def test_generate_flood_extents(caplog):
    hf_provider = hydrafloods_instance(["Sentinel-1"])
    dates = ["2022-10-05 01:25:51.000", "2022-10-05 01:25:26.000"]
    caplog.set_level(logging.INFO)
    hf_provider._generate_flood_extents(dates=dates, clip_ocean=True)
    assert "Generating flood extents for Sentinel-1 dataset" in caplog.text
    assert "Clipping image to country boundaries" in caplog.text
    assert "Applying edge-otsu thresholding"
    assert hasattr(hf_provider, "flood_extents")
    assert "Sentinel-1" in hf_provider.flood_extents
    caplog.set_level(logging.DEBUG)
    hf_provider = hydrafloods_instance(["Landsat 8"])
    hf_provider._generate_flood_extents()
    assert "Calculating MNDWI for Landsat 8" in caplog.text
    assert "Landsat 8" in hf_provider.flood_extents


def test_view_flood_extents():
    hf_provider = hydrafloods_instance(["Sentinel-1"])
    
    flood_map = hf_provider.view_flood_extents()
    assert isinstance(flood_map, geemap.Map)
    with pytest.raises( 
        TimeoutError,
        match="Plotting flood extents has timed out, increase the time out threshold or plot a smaller selection of your data",
    ):
        hf_provider.view_flood_extents(timeout=1)


def test_export_data(mocker):
    hf_provider = hydrafloods_instance(["Landsat 8"])

    mock_batch_export = mocker.patch("EO_Floods.providers.hydrafloods.hydrafloods.batch_export")
    hf_provider.export_data()
    assert mock_batch_export.call_count == 1
    hf_provider.export_data(include_base_data=True, scale=1000)
    assert mock_batch_export.call_count == 3

   
    
