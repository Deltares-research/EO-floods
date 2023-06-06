from interface.floodmap import FloodMap
from datetime import datetime

class FloodMapHF(FloodMap):
    
    def __init__(self, geometry, start_date: datetime, end_date: datetime, dataset: str) -> None:
        raise NotImplementedError

    
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
    
FloodMapHF(geometry="", start_date=datetime(2023, 4,3), end_date=datetime(2023, 4,4), dataset="S1")