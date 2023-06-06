from interface.floodmap import FloodMap
from datetime import datetime
from typing import Union

import hydrafloods as hf
import ee


class FloodMapHF(FloodMap):
    def __init__(
        self,
        geometry,
        start_date: str,
        end_date: str,
        dataset: Union[str, ee.ImageCollection],
        **dataset_kwargs
    ) -> None:
        self.geometry = geometry
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
            self.dataset = hf.Dataset.from_imgcollection(dataset, **dataset_kwargs)
        else:
            self.dataset = hf.Dataset(
                region=self.geometry,
                start_time=self.start_date,
                end_time=self.end_date,
                asset_id=dataset,
                **dataset_kwargs
            )

    def flood_extents(self):
        raise NotImplementedError

    def flood_depths(self):
        raise NotImplementedError

    def data_preview(self):
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


