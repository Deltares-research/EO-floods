from ipyleaflet import Map, WMSLayer, basemaps
from traitlets import Unicode
from ipywidgets import SelectionSlider

from typing import List

from EO_Floods.utils import get_centroid, get_dates_in_time_range

WMS_URL = "https://geoserver.gfm.eodc.eu/geoserver/gfm/wms"


class TimeWMSLayer(WMSLayer):
    time = Unicode("").tag(sync=True, o=True)


class WMS_MapObject:
    def __init__(
        self,
        start_date: str,
        end_date: str,
        layers: str,
        bbox: List[float],
        wms_url: str = WMS_URL,
    ):
        self.wms = TimeWMSLayer(
            url=wms_url,
            layers=layers,
            time=start_date,
            transparent=True,
            format="image/png",
        )
        self.start_date = start_date
        self.end_date = end_date
        self.bbox = bbox

    def map(self):
        centroid = get_centroid(self.bbox)
        m = Map(basemap=basemaps.CartoDB.Positron, center=centroid, zoom=9)
        m.add(self.wms)
        return m

    def get_slider(self):
        time_options = get_dates_in_time_range(self.start_date, self.end_date)
        self.slider = SelectionSlider(description="Time:", options=time_options)
        self.slider.observe(self.update_wms, "value")
        return self.slider

    def update_wms(self, change):
        self.wms.time = self.slider.value
