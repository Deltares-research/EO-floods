"""Dataset data classes for hydrafloods provider."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

import hydrafloods as hf
from pydantic import BaseModel

from EO_Floods.utils import calc_quality_score

if TYPE_CHECKING:
    import ee
logger = logging.getLogger(__name__)


class ImageryType(Enum):  # noqa: D101
    SAR = "SAR"
    OPTICAL = "optical"


class Dataset(BaseModel):  # noqa: D101
    name: str
    short_name: str
    default_flood_extent_algorithm: str
    imagery_type: ImageryType
    algorithm_params: dict
    visual_params: dict
    qa_band: str


class Sentinel1(Dataset):  # noqa: D101
    name: str = "Sentinel-1"
    short_name: str = "S1"
    imagery_type: ImageryType = ImageryType.SAR
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "VV", "invert": True, "initial_threshold": -16}}
    visual_params: dict = {"min": -25, "max": 0, "bands": ["VV"]}
    qa_band: str = "VV"
    providers: list = ["GFM", "Hydrafloods"]


class Sentinel2(Dataset):  # noqa: D101
    name: str = "Sentinel-2"
    short_name: str = "S2"
    imagery_type: ImageryType = ImageryType.OPTICAL
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "mndwi"}}
    visual_params: dict = {}
    qa_band: str = "swir1"
    providers: list = ["Hydrafloods"]


class Landsat7(Dataset):  # noqa: D101
    name: str = "Landsat 7"
    short_name: str = "L7"
    imagery_type: ImageryType = ImageryType.OPTICAL
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "mndwi"}}
    visual_params: dict = {"bands": ["swir1", "nir", "green"], "min": 0, "max": 0.5}
    qa_band: str = "swir1"
    providers: list = ["Hydrafloods"]


class Landsat8(Dataset):  # noqa: D101
    name: str = "Landsat 8"
    short_name: str = "L8"
    imagery_type: ImageryType = ImageryType.OPTICAL
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "mndwi"}}
    visual_params: dict = {"bands": ["swir1", "nir", "green"], "min": 0, "max": 0.5}
    qa_band: str = "swir1"
    providers: list = ["Hydrafloods"]


class VIIRS(Dataset):  # noqa: D101
    name: str = "VIIRS"
    short_name: str = "VIIRS"
    imagery_type: ImageryType = ImageryType.OPTICAL
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "mndwi"}}
    visual_params: dict = {}
    qa_band: str = "swir1"
    providers: list = ["Hydrafloods"]


class MODIS(Dataset):  # noqa: D101
    name: str = "MODIS"
    short_name: str = "MODIS"
    imagery_type: ImageryType = ImageryType.OPTICAL
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "mndwi"}}
    visual_params: dict = {}
    qa_band: str = "swir1"
    providers: list = ["Hydrafloods"]


DATASETS = {
    "Sentinel-1": Sentinel1(),
    "Sentinel-2": Sentinel2(),
    "Landsat 7": Landsat7(),
    "Landsat 8": Landsat8(),
    "VIIRS": VIIRS(),
    "MODIS": MODIS(),
}


class HydraFloodsDataset:
    """Wrapper for Hydrafloods dataset data classes."""

    def __init__(
        self,
        dataset: Dataset,
        region: ee.geometry.Geometry,
        start_date: str,
        end_date: str,
        **kwargs: dict[str],
    ) -> None:
        """Class for initializing Hydrafloods datasets.

        Parameters
        ----------
        dataset : Dataset
            EO_Floods.Dataset object containing information on the dataset and configuration
            for processing.
        region : ee.geometry.Geometry
            Earth Engine geometry that represents the area of interest.
        start_date : str
            Start date of the time window of interest (YYY-mm-dd).
        end_date : str
            End date of the time window of interest (YYY-mm-dd).
        kwargs: dict
            key word arguments to pass to hydrafloods dataset intialization.

        """
        hf_datasets = {
            "Sentinel-1": hf.Sentinel1,
            "Sentinel-2": hf.Sentinel2,
            "Landsat 7": hf.Landsat7,
            "Landsat 8": hf.Landsat8,
            "VIIRS": hf.Viirs,
            "MODIS": hf.Modis,
        }
        self.name: str = dataset.name
        self.short_name: str = dataset.short_name
        self.imagery_type: ImageryType = dataset.imagery_type
        self.default_flood_extent_algorithm: str = dataset.default_flood_extent_algorithm
        self.region = region
        self.qa_band = dataset.qa_band
        self.algorithm_params: dict = dataset.algorithm_params
        self.visual_params: dict = dataset.visual_params
        self.providers = dataset.providers
        self.obj: hf.Dataset = hf_datasets[dataset.name](
            region=region,
            start_time=start_date,
            end_time=end_date,
            **kwargs,
        )
        logger.debug("Initialized hydrafloods dataset for %s", self.name)

    def quality_score(self) -> list[float]:
        """Calculate a quality score for satellite images.

        Quality score is the percentage of unmasked pixels present in the whole image.


        Returns
        -------
        list[float]
           list of quality scores for every image in the dataset.

        """
        if self.name in [
            "VIIRS",
            "MODIS",
        ]:  # these datasets consist of global images, need to be clipped first before reducing
            self.obj.apply_func(func=lambda x: x.clip(self.region), inplace=True)
        self.obj.apply_func(func=calc_quality_score, inplace=True, band=self.qa_band)
        qa_score = self.obj.collection.aggregate_array("qa_score").getInfo()
        return [round(score, 2) for score in qa_score]
