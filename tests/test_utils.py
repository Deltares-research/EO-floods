import pytest
import hydrafloods as hf

from EO_Floods.utils import (
    coords_to_ee_geom,
    calc_quality_score,
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


class TestCalcQualityScore:
    STARTDATE = "2022-10-01"
    ENDDATE = "2022-10-30"
    REGION = coords_to_ee_geom([67.740187, 27.712453, 68.104933, 28.000935])

    def test_l8_qa(self):
        l8 = hf.Landsat8(
            region=self.REGION, start_time=self.STARTDATE, end_time=self.ENDDATE
        )
        l8.apply_func(calc_quality_score, inplace=True, band="swir1")
        qa_scores = l8.collection.aggregate_array("qa_score").getInfo()
        assert len(qa_scores) == l8.n_images

    def test_l7_qa(self):
        l7 = hf.Landsat7(self.REGION, self.STARTDATE, self.ENDDATE)
        l7.apply_func(calc_quality_score, inplace=True, band="swir1")
        qa_scores = l7.collection.aggregate_array("qa_score").getInfo()
        assert len(qa_scores) == l7.n_images

    def test_s1_qa(self):
        s1 = hf.Sentinel1(self.REGION, self.STARTDATE, self.ENDDATE)
        s1.apply_func(calc_quality_score, inplace=True, band="VV")
        qa_scores = s1.collection.aggregate_array("qa_score").getInfo()
        assert len(qa_scores) == s1.n_images

    def test_modis_qa(self):
        modis = hf.Modis(self.REGION, self.STARTDATE, self.ENDDATE)
        modis.apply_func(lambda x: x.clip(self.REGION), inplace=True)
        modis.apply_func(calc_quality_score, inplace=True, band="swir1")
        qa_scores = modis.collection.aggregate_array("qa_score").getInfo()
        assert len(qa_scores) == modis.n_images

    def test_viirs(self):
        viirs = hf.Viirs(self.REGION, self.STARTDATE, self.ENDDATE)
        viirs.apply_func(lambda x: x.clip(self.REGION), inplace=True)
        viirs.apply_func(calc_quality_score, inplace=True, band="swir1")
        qa_scores = viirs.collection.aggregate_array("qa_score").getInfo()
        assert len(qa_scores) == viirs.n_images


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
        ValueError, match=f"'{dates[0]}' not in {start_date}-{end_date} daterange"
    ):
        dates_within_daterange(dates=dates, start_date=start_date, end_date=end_date)

    dates = ["1996-03-10 00:01:00", "1996-03-11 00:54:00"]
    assert dates_within_daterange(dates=dates, start_date=start_date, end_date=end_date)
