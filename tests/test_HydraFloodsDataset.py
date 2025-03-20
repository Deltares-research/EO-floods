import hydrafloods as hf
from eo_floods.providers.hydrafloods.dataset import HydraFloodsDataset
from eo_floods.utils import coords_to_ee_geom

class TestCalcQualityScore:
    STARTDATE = "2022-10-01"
    ENDDATE = "2022-10-30"
    REGION = coords_to_ee_geom([67.740187, 27.712453, 68.104933, 28.000935])

    def test_l8_q(self):
        l8 = hf.Landsat8(
            region=self.REGION, start_time=self.STARTDATE, end_time=self.ENDDATE
        )
        l8.apply_func(HydraFloodsDataset._calculate_quality_score, inplace=True, band="swir1")
        q_scores = l8.collection.aggregate_array("q_score").getInfo()
        assert len(q_scores) == l8.n_images

    def test_l7_q(self):
        l7 = hf.Landsat7(self.REGION, self.STARTDATE, self.ENDDATE)
        l7.apply_func(HydraFloodsDataset._calculate_quality_score, inplace=True, band="swir1")
        q_scores = l7.collection.aggregate_array("q_score").getInfo()
        assert len(q_scores) == l7.n_images

    def test_s1_q(self):
        s1 = hf.Sentinel1(self.REGION, self.STARTDATE, self.ENDDATE)
        s1.apply_func(HydraFloodsDataset._calculate_quality_score, inplace=True, band="VV")
        q_scores = s1.collection.aggregate_array("q_score").getInfo()
        assert len(q_scores) == s1.n_images

    def test_modis_q(self):
        modis = hf.Modis(self.REGION, self.STARTDATE, self.ENDDATE)
        modis.apply_func(lambda x: x.clip(self.REGION), inplace=True)
        modis.apply_func(HydraFloodsDataset._calculate_quality_score, inplace=True, band="swir1")
        q_scores = modis.collection.aggregate_array("q_score").getInfo()
        assert len(q_scores) == modis.n_images

    def test_viirs(self):
        viirs = hf.Viirs(self.REGION, self.STARTDATE, self.ENDDATE)
        viirs.apply_func(lambda x: x.clip(self.REGION), inplace=True)
        viirs.apply_func(HydraFloodsDataset._calculate_quality_score, inplace=True, band="swir1")
        q_scores = viirs.collection.aggregate_array("q_score").getInfo()
        assert len(q_scores) == viirs.n_images
