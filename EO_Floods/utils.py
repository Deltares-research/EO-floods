from typing import List, Tuple
import logging

import ee
import datetime
from dateutil import parser

log = logging.getLogger(__name__)


def coords_to_ee_geom(coords: list) -> ee.geometry.Geometry:
    if len(coords) == 4:
        xmin, ymin, xmax, ymax = coords
        if not -180 <= xmin <= 180 or not -180 <= xmax <= 180:
            raise ValueError("X values are not within the longitudinal range")
        if not -90 <= ymin <= 90 or not -90 <= ymax <= 90:
            raise ValueError("Y values are not within the latitudinal range")
        return ee.Geometry.BBox(xmin, ymin, xmax, ymax)

    return ee.Geometry.Polygon(coords)


def filter_ee_imgcollection_by_geom(
    imgcollection: ee.ImageCollection,
    start_date: str,
    end_date: str,
    filter_geom: ee.Geometry,
):
    return imgcollection.filterBounds(filter_geom).filterDate(start_date, end_date)


def date_parser(date_string: str) -> datetime.datetime:
    """Parses a date string and returns a datetime object.

    Args:
        date_string (str): A string representing a date in various formats.

    Returns:
        datetime.datetime or None: A datetime object representing the parsed date
        if the input string is in a valid date format, or None if the input string
        does not represent a valid date."""
    try:
        # Parse the date string and return the datetime object
        parsed_date = parser.parse(date_string)
        return parsed_date
    except ValueError:
        raise ValueError("Invalid date string format")


def get_centroid(geometry: List[float]) -> Tuple[float]:
    x1, y1, x2, y2 = geometry
    return ((y1 + y2) / 2, (x1 + x2) / 2)
