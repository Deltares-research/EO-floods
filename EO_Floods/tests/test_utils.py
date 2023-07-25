import pytest

from EO_Floods.utils import coords_to_ee_geom


def test_coords_to_geom():
    coords = [-179, 78, -177, 89]
    geom = coords_to_ee_geom(coords)
    geom_coords = geom.coordinates().getInfo()[0]
    # flatten list of coords
    coordinates = list(
        set([coord for coordspair in geom_coords for coord in coordspair])
    )
    coordinates.sort()
    coords.sort()
    assert coords == coordinates

    # test value errors for coordinates outside of longitude/latitude range
    with pytest.raises(
        ValueError, match=r"X values are not within the longitudinal range"
    ):
        coords = [-181, 78, -177, 89]
        geom = coords_to_ee_geom(coords)
    with pytest.raises(
        ValueError, match=r"Y values are not within the latitudinal range"
    ):
        coords = [-179, 78, -177, 91]
        geom = coords_to_ee_geom(coords)
