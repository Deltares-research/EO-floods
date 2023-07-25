from datetime import datetime
from typing import Union

import hydrafloods as hf
import ee
from shapely.geometry import Polygon

from EO_Floods.interface.floodmap import FloodMap
from EO_Floods.utils import coords_to_ee_geom, filter_ee_imgcollection


class FloodMapHF(FloodMap):
    def __init__(
        self,
        geometry,
        start_date: str,
        end_date: str,
        dataset: Union[str, ee.ImageCollection],
        **dataset_kwargs
    ) -> None:
        self.geometry = coords_to_ee_geom(geometry)
        self.start_date = start_date
        self.end_date = end_date

        hf_datasets = {
            "Sentinel 1": hf.Sentinel1,
            "Sentinel 2": hf.Sentinel2,
            "Landsat 8": hf.Landsat8,
            "Landsat 7": hf.Landsat7,
            "VIIRS": hf.Viirs,
            "MODIS": hf.Modis,
        }
        if dataset in hf_datasets:
            self.dataset = hf_datasets[dataset](
                region=self.geometry,
                start_time=self.start_date,
                end_time=self.end_date,
                **dataset_kwargs
            )
        elif isinstance(dataset, ee.ImageCollection):
            imgcollection = filter_ee_imgcollection(
                dataset, start_date, end_date, self.geometry
            )
            self.dataset = hf.Dataset.from_imgcollection(
                imgcollection, **dataset_kwargs
            )
        else:
            self.dataset = hf.Dataset(
                region=self.geometry,
                start_time=self.start_date,
                end_time=self.end_date,
                asset_id=dataset,
                **dataset_kwargs
            )

    def data_preview(self):
        return {
            "dataset_id": self.dataset.asset_id,
            "n_images": self.dataset.n_images,
            "dates": self.dataset.dates,
        }

    def flood_extents(self):
        raise NotImplementedError

    def flood_depths(self):
        raise NotImplementedError

    def maximum_extent(self):
        raise NotImplementedError

    def maximum_duration(self):
        raise NotImplementedError

    def maximum_depth(self):
        raise NotImplementedError

    def metrics(self):
        raise NotImplementedError

    def export_data(self):
        raise NotImplementedError
