"""utils module."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import ee
from dateutil import parser

log = logging.getLogger(__name__)


def coords_to_ee_geom(coords: list) -> ee.geometry.Geometry:
    """Convert a list of xmin, ymin, xmax, ymax coords to an ee.Geometry."""
    if len(coords) == 4:  # noqa:PLR2004
        xmin, ymin, xmax, ymax = coords
        if not -180 <= xmin <= 180 or not -180 <= xmax <= 180:  # noqa:PLR2004
            err_msg = "X values are not within the longitudinal range"
            raise ValueError(err_msg)
        if not -90 <= ymin <= 90 or not -90 <= ymax <= 90:  # noqa:PLR2004
            err_msg = "Y values are not within the latitudinal range"
            raise ValueError(err_msg)
        return ee.Geometry.BBox(xmin, ymin, xmax, ymax)

    return ee.Geometry.Polygon(coords)


def date_parser(date_string: str) -> datetime:
    """Parse a datetime object from a string.

    Parameters
    ----------
    date_string : str
        string containing datetime

    Returns
    -------
    datetime
        datetime object

    """
    try:
        # Parse the date string and return the datetime object
        parsed_date = parser.parse(date_string)
    except ValueError as e:
        err_msg = "Invalid date string format"
        raise ValueError(err_msg) from e
    return parsed_date


def get_centroid(bounding_box: list[float]) -> tuple[float]:
    """Calculate centroid given a bounding box with xmin, ymin, xmax, ymax coordinates.

    Parameters
    ----------
    bounding_box : list[float]
        bounding box with xmin, ymin, xmax, ymax coordinates

    Returns
    -------
    tuple[float]
        centroid in (y,x) coordinates.

    """
    x1, y1, x2, y2 = bounding_box
    return ((y1 + y2) / 2, (x1 + x2) / 2)


def coords_to_geojson(coords: list[float]) -> dict:
    """Convert a list of coordinates to a GeoJSON dictionary.

    Parameters
    ----------
    coords : list[float]
        List of coordinates in the format [x_min, y_min, x_max, y_max].

    Returns
    -------
    dict
        GeoJSON dictionary representing the bounding box.

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
                ],
            ],
        },
    )

    return geojson_dict[0]


def get_dates_in_time_range(start_date_str: str, end_date_str: str) -> list:
    """Generate a list of dates between start_date_str and end_date_str (inclusive).

    Parameters
    ----------
    start_date_str : str
        Start date in the format "year-month-day".
    end_date_str :  str
        End date in the format "year-month-day".

    Returns
    -------
    list
        List of dates in the format "year-month-day".

    """
    # Convert start and end date strings to datetime objects
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")  # noqa:DTZ007
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")  # noqa:DTZ007

    # Initialize an empty list to store the dates
    date_list = []

    # Iterate through the dates from start_date to end_date
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    return date_list


def dates_within_daterange(dates: list[str], start_date: str, end_date: str) -> bool:
    """Check if dates within a given date range.

    Parameters
    ----------
    dates : list[str]
        list of dates to check
    start_date : str
        start date of the date range
    end_date : str
        end date of the date range

    Returns
    -------
    bool
        boolean

    """
    start_date_ts = date_parser(start_date)
    end_date_ts = date_parser(end_date)
    if start_date >= end_date:
        err_msg = f"Start date '{start_date}' must occur before end date '{end_date}'"
        raise ValueError(err_msg)

    for date in dates:
        if not start_date_ts <= date_parser(date) <= end_date_ts:
            err_msg = f"Start date '{start_date}' must occur before end date '{end_date}'"
            raise ValueError(err_msg)
    return True
