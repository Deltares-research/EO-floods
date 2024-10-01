"""Mapping class for creating WMS ipyleaflet timeseries maps."""

from __future__ import annotations

from ipyleaflet import Map, WidgetControl, WMSLayer, basemaps
from ipywidgets import SelectionSlider
from traitlets import Unicode

from EO_Floods.utils import get_centroid, get_dates_in_time_range

WMS_URL = "https://geoserver.gfm.eodc.eu/geoserver/gfm/wms"


class TimeWMSLayer(WMSLayer):
    """Time series wrapper for WMSLayer."""

    time = Unicode("").tag(sync=True, o=True)


class WMSMap:
    """Class for creating ipyleaflet WMS maps with a time slider."""

    def __init__(
        self,
        start_date: str,
        end_date: str,
        layers: str | list[str],
        bbox: list[float],
        wms_url: str = WMS_URL,
    ) -> None:
        """Instantiate a WMSMap object.

        Parameters
        ----------
        start_date : str
            start date of timeseries
        end_date : str
            end date of timeseries
        layers : str or list[str]
            name of map layers
        bbox : list[float]
            bounding box in [xmin, ymin, xmax, ymax] format
        wms_url : str, optional
            url of the WMS, by default WMS_URL

        """
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

    def get_map(self) -> Map:
        """Create a WMS map with a time slider.

        Returns
        -------
        Map
            ipyleaflet map instance

        """
        centroid = get_centroid(self.bbox)
        m = Map(basemap=basemaps.OpenStreetMap.Mapnik, center=centroid, zoom=9)
        m.add(self.wms)
        self.slider = self._get_slider()
        self.slider.observe(self._update_wms, "value")
        slider_cntrl = WidgetControl(widget=self.slider, position="bottomright")
        m.add(slider_cntrl)
        return m

    def _get_slider(self) -> SelectionSlider:
        time_options = get_dates_in_time_range(self.start_date, self.end_date)
        return SelectionSlider(description="Time:", options=time_options)

    def _update_wms(self, value) -> None:
        self.wms.time = self.slider.value
