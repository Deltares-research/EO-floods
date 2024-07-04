import pytest
from EO_Floods.providers.hydrafloods.auth import ee_initialize
from EO_Floods.floodmap import FloodMap

ee_initialize()


@pytest.fixture()
def flood_map() -> FloodMap:
    return FloodMap(
        start_date="2022-10-01",
        end_date="2022-10-15",
        geometry=[67.740187, 27.712453, 68.104933, 28.000935],
    )
