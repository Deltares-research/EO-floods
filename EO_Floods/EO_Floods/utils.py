import ee


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
