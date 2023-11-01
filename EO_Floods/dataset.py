from pydantic import BaseModel
from enum import Enum


class ImageryType(Enum):
    SAR = "SAR"
    OPTICAL = "optical"


class Dataset(BaseModel):
    name: str
    default_flood_extent_algorithm: str
    imagery_type: ImageryType
    algorithm_params: dict
    visual_params: dict


class Sentinel1(Dataset):
    name = "Sentinel-1"
    imagery_type = ImageryType.SAR
    default_flood_extent_algorithm = "edge_otsu"
    algorithm_params = {"edge_otsu": {"band": "VV"}}
    visual_params = {"min": -25, "max": 0, "bands": ["VV"]}


class Sentinel2(Dataset):
    name = "Sentinel-2"
    imagery_type = ImageryType.OPTICAL
    default_flood_extent_algorithm = "edge_otsu"
    algorithm_params = {"edge_otsu": {"band": "mndwi"}}
    visual_params = {}


class Landsat7(Dataset):
    name = "Landsat 7"
    imagery_type = ImageryType.OPTICAL
    default_flood_extent_algorithm = "edge_otsu"
    algorithm_params = {"edge_otsu": {"band": "mndwi"}}
    visual_params = {}


class Landsat8(Dataset):
    name = "Landsat 8"
    imagery_type = ImageryType.OPTICAL
    default_flood_extent_algorithm = "edge_otsu"
    algorithm_params = {"edge_otsu": {"band": "mndwi"}}
    visual_params = {}


class VIIRS(Dataset):
    name = "VIIRS"
    imagery_type = ImageryType.OPTICAL
    default_flood_extent_algorithm = "edge_otsu"
    algorithm_params = {"edge_otsu": {"band": "mndwi"}}
    visual_params = {}


class MODIS(Dataset):
    name = "MODIS"
    imagery_type = ImageryType.OPTICAL
    default_flood_extent_algorithm = "edge_otsu"
    algorithm_params = {"edge_otsu": {"band": "mndwi"}}
    visual_params = {}


DATASETS = {
    "Sentinel-1": Sentinel1(),
    "Sentinel-2": Sentinel2(),
    "Landsat 7": Landsat7(),
    "Landsat 8": Landsat8(),
    "VIIRS": VIIRS(),
    "MODIS": MODIS(),
}
