from pydantic import BaseModel
from enum import Enum


class ImageryType(Enum):
    SAR = "SAR"
    OPTICAL = "optical"


class Dataset(BaseModel):
    name: str
    short_name: str
    default_flood_extent_algorithm: str
    imagery_type: ImageryType
    algorithm_params: dict
    visual_params: dict
    qa_band: str


class Sentinel1(Dataset):
    name: str = "Sentinel-1"
    short_name: str = "S1"
    imagery_type: ImageryType = ImageryType.SAR
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "VV"}}
    visual_params: dict = {"min": -25, "max": 0, "bands": ["VV"]}
    qa_band: str = "VV"


class Sentinel2(Dataset):
    name: str = "Sentinel-2"
    short_name: str = "S2"
    imagery_type: ImageryType = ImageryType.OPTICAL
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "mndwi"}}
    visual_params: dict = {}
    qa_band: str = "swir1"


class Landsat7(Dataset):
    name: str = "Landsat 7"
    short_name: str = "L7"
    imagery_type: ImageryType = ImageryType.OPTICAL
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "mndwi"}}
    visual_params: dict = {"bands": ["swir1", "nir", "green"], "min": 0, "max": 0.5}
    qa_band: str = "swir1"


class Landsat8(Dataset):
    name: str = "Landsat 8"
    short_name: str = "L8"
    imagery_type: ImageryType = ImageryType.OPTICAL
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "mndwi"}}
    visual_params: dict = {"bands": ["swir1", "nir", "green"], "min": 0, "max": 0.5}
    qa_band: str = "swir1"


class VIIRS(Dataset):
    name: str = "VIIRS"
    short_name: str = "VIIRS"
    imagery_type: ImageryType = ImageryType.OPTICAL
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "mndwi"}}
    visual_params: dict = {}
    qa_band: str = "swir1"


class MODIS(Dataset):
    name: str = "MODIS"
    short_name: str = "MODIS"
    imagery_type: ImageryType = ImageryType.OPTICAL
    default_flood_extent_algorithm: str = "edge_otsu"
    algorithm_params: dict = {"edge_otsu": {"band": "mndwi"}}
    visual_params: dict = {}
    qa_band: str = "swir1"


DATASETS = {
    "Sentinel-1": Sentinel1(),
    "Sentinel-2": Sentinel2(),
    "Landsat 7": Landsat7(),
    "Landsat 8": Landsat8(),
    "VIIRS": VIIRS(),
    "MODIS": MODIS(),
}
