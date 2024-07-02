from typing import List, Tuple, Optional
import logging
from datetime import datetime, timedelta

import ee

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


def date_parser(date_string: str) -> datetime:
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


def get_centroid(geometry: List[float]) -> Tuple[float, float]:
    x1, y1, x2, y2 = geometry
    return ((y1 + y2) / 2, (x1 + x2) / 2)


def coords_to_geojson(coords: List[float]) -> dict:
    """
    Converts a list of coordinates to a GeoJSON dictionary.

    Args:
        coords_list (list): List of coordinates in the format [x_min, y_min, x_max, y_max].

    Returns:
        dict: GeoJSON dictionary representing the bounding box.
    """
    x_min, y_min, x_max, y_max = coords

    geojson_dict = (
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [x_min, y_min],
                    [x_max, y_min],
                    [x_max, y_max],
                    [x_min, y_max],
                    [x_min, y_min],
                ]
            ],
        },
    )

    return geojson_dict[0]


def get_dates_in_time_range(start_date_str: str, end_date_str: str) -> list:
    """
    Generates a list of dates between start_date_str and end_date_str (inclusive).

    Args:
        start_date_str (str): Start date in the format "year-month-day".
        end_date_str (str): End date in the format "year-month-day".

    Returns:
        list: List of dates in the format "year-month-day".
    """
    # Convert start and end date strings to datetime objects
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    # Initialize an empty list to store the dates
    date_list = []

    # Iterate through the dates from start_date to end_date
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    return date_list


def calc_quality_score(
    image: ee.Image, band: str, geom: Optional[ee.Geometry] = None
) -> ee.Image:
    if not geom:
        geom = ee.Geometry(ee.Image(image).select(band).geometry())
    masked_pixel_count = (
        image.select(band)
        .reduceRegion(
            reducer=ee.Reducer.count(), geometry=geom, scale=30, maxPixels=1e10
        )
        .get(band)
    )
    total_pixel_count = (
        image.select(band)
        .unmask()
        .reduceRegion(
            reducer=ee.Reducer.count(), geometry=geom, scale=30, maxPixels=1e10
        )
        .get(band)
    )
    qa_score = ee.Number(masked_pixel_count).divide(total_pixel_count).multiply(100)
    return image.set({"qa_score": qa_score})


def dates_within_daterange(dates: List[str], start_date: str, end_date: str) -> bool:
    start_date_ts = date_parser(start_date)
    end_date_ts = date_parser(end_date)
    if start_date >= end_date:
        raise ValueError(
            f"Start date '{start_date}' must occur before end date '{end_date}'"
        )

    for date in dates:
        if not start_date_ts <= date_parser(date) <= end_date_ts:
            raise ValueError(f"'{date}' not in {start_date}-{end_date} daterange")
    return True
