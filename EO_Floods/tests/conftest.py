import pytest
from EO_Floods.floodmap_hf import FloodMapHF


@pytest.fixture
def hf_floodmap_S1():
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
    return floodmap
