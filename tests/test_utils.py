import pytest

from eo_floods.utils import (
    coords_to_ee_geom,
    dates_within_daterange,
)


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




def test_dates_within_range():
    dates = ["1996-03-10", "1996-03-11", "1996-03-12"]
    start_date = "1996-03-10"
    end_date = "1996-03-12"
    assert dates_within_daterange(dates=dates, start_date=start_date, end_date=end_date)

    with pytest.raises(
        ValueError,
        match="Start date '2022-01-02' must occur before end date '2022-01-01'",
    ):
        dates_within_daterange(
            dates=dates, start_date="2022-01-02", end_date="2022-01-01"
        )

    dates.insert(0, "1995-03-10")
    with pytest.raises(
        ValueError, match="Start date '1996-03-10' must occur before end date '1996-03-12'"
    ):
        dates_within_daterange(dates=dates, start_date=start_date, end_date=end_date)

    dates = ["1996-03-10 00:01:00", "1996-03-11 00:54:00"]
    assert dates_within_daterange(dates=dates, start_date=start_date, end_date=end_date)
