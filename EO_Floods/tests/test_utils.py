from EO_Floods.utils import coords_to_ee_geom

def test_coords_to_geom():
    coords = [-179, 78, -177, 89]
    geom = coords_to_ee_geom(coords)
    assert geom.north == 89
    assert geom.south == 78
    assert geom.west == -179
    assert geom.east == -177



