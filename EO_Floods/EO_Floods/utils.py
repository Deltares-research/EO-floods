import ee
import datetime


def coords_to_ee_geom(coords: list):
    if len(coords) == 4:
        xmin, ymin, xmax, ymax = coords
        if not -180 <= xmin <= 180 or not -180 <= xmax <= 180:
            raise ValueError("X values are not within the longitudinal range")
        if not -90 <= ymin <= 90 or not -90 <= ymax <= 90:
            raise ValueError("Y values are not within the latitudinal range")
        return ee.Geometry.BBox(xmin, ymin, xmax, ymax)

    return ee.Geometry.Polygon(coords)


def filter_ee_imgcollection(
    imgcollection: ee.ImageCollection,
    start_date: str,
    end_date: str,
    filter_geom: ee.Geometry,
):
    return imgcollection.filterBounds(filter_geom).filterDate(start_date, end_date)


def decode_date(date):
    """Decodes a date from a command line argument, returning msec since epoch".

    args:
        date (str): date value in a format that can be parsed into datetime object

    returns:
        datetime.datetime: decoded datetime value

    raises:
        TypeError: if string does not conform to a legal date format.
    """

    date_formats = [
        "%Y%m%d",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
    ]
    for date_format in date_formats:
        try:
            dt = datetime.datetime.strptime(date, date_format)
            return dt
        except ValueError:
            continue
    raise TypeError(f"Invalid value for property of type 'date': '{date}'.")
