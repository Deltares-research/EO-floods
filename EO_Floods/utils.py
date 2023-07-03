from typing import Union
import ee
from shapely.geometry import Polygon, box


def geom_to_ee_geom(geometry: list):
    if len(geometry) == 4:
        xmin, ymin, xmax, ymax = geometry
        if xmin > 180 or xmax > 180 or xmin < -180 or xmax < -180:
            raise ValueError("X values are not within the longitudinal range")
        if ymin > 90 or ymax > 90 or ymin < -90 or ymax < -90:
            raise ValueError("Y values are not within the latitudinal range")
        return ee.Geometry.BBox(xmin, ymin, xmax, ymax)

    return ee.Geometry.Polygon(geometry)
