import requests
from datetime import datetime, timedelta

from retry import retry
import pandas as pd
import geopandas as gpd
import numpy as np
import numba
from numba import jit, njit
from shapely.geometry import box


def get_overpasses(track_ids):
    """Retrieves all overpasses for the given track ids

    :param track_ids: list of icesat2 track ids
    :type track_ids: list
    :return: A list of lists containing the icesat2 track ids and the
    corresponding dates
    :rtype: list
    """

    trackdates_url = "https://openaltimetry.org/data/icesat2/getTrackDate"
    dates = api_get_call(trackdates_url)
    overpasses = []
    for track_id in track_ids:
        for track_date in dates["track_{}".format(track_id)].split(","):
            overpasses.append([track_date, track_id])
    return overpasses


def get_track_ids(coordinates):
    """Retrieves icesat2 track ids for a given bounding box"

    :param coordinates: tuple of min and max xy coordinates of a bounding box
    :type coordinates: tuple of floats
    :return: list of track ids
    :rtype: list
    """
    minx, miny, maxx, maxy = coordinates
    tracks_url = f"https://openaltimetry.org/data/api/icesat2/getTracks?minx={minx}&miny={miny}&maxx={maxx}&maxy={maxy}&outputFormat=json"
    data = api_get_call(tracks_url)
    return data["output"]["track"]


def get_icesat2_data_from_OA_api(
    icesat2_product: str,
    boundingbox: list,
    track_date: str,
    track_id: str,
    series_included=["Medium", "High"],
) -> dict:
    series_included = "".join(
        ["photonConfidence[]=" + series.lower() for series in series_included]
    )
    minx, miny, maxx, maxy = boundingbox
    OA_API_URL = (
        "https://openaltimetry.org/data/api/icesat2/{}?"
        "&minx={}&miny={}&maxx={}&maxy={}&date={}&trackId={}&{}"
        "&beamName=gt3r&beamName=gt3l&beamName=gt2r&beamName=gt2l&beamName=gt1r&beamName=gt1l".format(
            icesat2_product,
            minx,
            miny,
            maxx,
            maxy,
            track_date,
            track_id,
            series_included,
        )
    )
    return api_get_call(OA_API_URL)


@retry(delay=5, tries=10)
def api_get_call(url):
    """Makes an api get request with retries.

    :param url: url string for making a get request
    :type url: str
    :return: request response as JSON
    :rtype: dict
    """
    with requests.get(url) as response:
        return response.json()


def parse_atl08(photon_data: dict, track_id: str, track_date: str) -> list:
    """Parses a dictionary containing data on the atl08 icesat2 product. The dictionary must be
    from the response of the open altimetry API request for requesting icesat2 data.

        :param photon_data: Dictionary containing icesat2 atl08 data
        :type photon_data: dict
        :param track_id: the id of the icesat2 track
        :type track_id: str
        :param track_date: the date of the track
        :type track_date: str
        :return: a list of dict with the icesat2 data
        :rtype: list of dicts
    """

    rows = []
    for beam in photon_data["series"]:
        beam_name = beam["beam"]
        isStrongBeam = beam["isStrongBeam"]
        for lle in beam["lat_lon_elev_canopy"]:
            row = {
                "track_id": track_id,
                "date": track_date,
                "beam": beam_name,
                "isStrongBeam": isStrongBeam,
                "lon": round(lle[1], 6),
                "lat": round(lle[0], 6),
                "h": lle[2],
            }
            rows.append(row)
    return rows


def parse_atl03(photon_data: dict, track_id: str, track_date: str) -> list:
    """Parses a dictionary containing data on the atl03 icesat2 product. The dictionary must
    be from the response of the open altimetry API request for requesting icesat2 data.

    :param photon_data: Dictionary containing icesat2 atl03 data
    :type photon_data: dict
    :param track_id: the id of the icesat2 track
    :type track_id: str
    :param track_date: the date of the track
    :type track_date: str
    :return: a list of dict with the icesat2 data
    :rtype: list of dicts
    """
    rows = []

    for beam in photon_data:
        beam_name = beam["beam_name"]
        for s in beam["series"]:
            # every series has name (confidence)
            series_name = s["name"]
            for o in s["data"]:
                # add rows
                row = {
                    "track_id": track_id,
                    "date": track_date,
                    "beam": beam_name,
                    "series": series_name,
                    "lon": round(o[1], 6),
                    "lat": round(o[0], 6),
                    "h": o[2],
                }

                rows.append(row)
    return rows


def expand_dates(dates):
    expanded_dates = []
    for date in dates:
        date_1 = datetime.strptime(date, "%Y-%m-%d")
        date_0 = date_1 - timedelta(days=1)
        date_2 = date_1 + timedelta(days=1)
        expanded_dates.append(date_0)
        expanded_dates.append(date_1)
        expanded_dates.append(date_2)
    expanded_dates = list(
        set([datetime.strftime(date, "%Y-%m-%d") for date in expanded_dates])
    )
    return expanded_dates


def rewrite_dates(dates):
    return [
        datetime.strftime(datetime.strptime(date, "%d-%m-%Y"), "%Y-%m-%d")
        for date in dates
    ]


def date_checker(aoi: list, dates: list):
    dates = rewrite_dates(dates)

    track_ids = get_track_ids(aoi)
    overpasses = get_overpasses(track_ids)
    matched_dates = []
    df = pd.DataFrame()
    dates = expand_dates(dates)
    for date in dates:
        for overpass in overpasses:
            if date in overpass[0]:
                matched_dates.append(overpass)
    if matched_dates:
        for date, trackid in matched_dates:
            data = get_icesat2_data_from_OA_api(
                "atl08", aoi, track_date=date, track_id=trackid
            )

            rows = parse_atl08(data, track_id=trackid, track_date=date)
            if rows:
                print(f"icesat2 data found for {date}")
                df_rows = pd.DataFrame(rows)

                df = pd.concat([df, df_rows])
                df.drop_duplicates(inplace=True)

        return df
    else:
        print("no icesat2 data found for these dates")


def get_bounding_box(aoi: gpd.GeoDataFrame, icesat2_product: str) -> list:
    """Creates a bounding box for a given geodataframe. If the icesat product is
    atl03 the size of the bounding box is checked. If the size is bigger than 1
    degree on any axis, the bounding box is cut up in smaller tiles.

    :param aoi: a geodataframe containing a reservoir geometry.
    :type aoi: gpd.GeoDataFrame
    :return: list of bounding boxes, if just one bounding box, the function still
        returns a list of size one.
    """
    minx, miny, maxx, maxy = aoi.loc[0, "geometry"].bounds
    bounding_box = (minx, miny, maxx, maxy)
    if (maxx - minx + maxy - miny) > 1 and icesat2_product == "atl03":
        bounding_box = bounding_box_tiles(bounding_box, step_size=0.5)
    else:
        bounding_box = [bounding_box]
    return bounding_box


def bounding_box_tiles(bbox_coords, step_size):
    """Divides a bounding box to smaller bounding boxes given a stepsize

    :param bbox_coords: The min x, min y, max x, and max y of a bounding box
    :type bbox_coords: tuple or list
    :param step_size: The length of the smaller bounding boxes
    :type step_size: float
    :return: list of bounding boxes with min x, min y, max x, max y coordinates
    :rtype: list
    """
    minx, miny, maxx, maxy = bbox_coords
    box_list = []
    for y in np.arange(miny, maxy, step_size):
        for x in np.arange(minx, maxx, step_size):
            xmin = x
            ymin = y
            xmax = x + step_size
            ymax = y + step_size
            box = [xmin, ymin, xmax, ymax]
            box_list.append(box)
    return box_list


@njit(parallel=True)
def points_in_polygon_parallel(
    coordinates: np.ndarray, polygon: np.ndarray
) -> np.ndarray:
    """This function uses a parallelized approach for determining whether multiple
    points are within a polygon.

    :param coordinates: list of coordinate pairs of points
    :type coordinates: np.ndarray
    :param polygon: collection of points forming a polygon
    :type polygon: np.ndarray
    :return: A boolean array with the same length of the list point coordinates
    :rtype: np.ndarry
    """

    ln = len(coordinates)
    D = np.empty(ln, dtype=numba.boolean)
    for i in numba.prange(ln):
        coords = coordinates[i]
        D[i] = point_in_polygon(polygon, coords)
    return D


@jit(nopython=True)
def point_in_polygon(polygon, point):
    length = len(polygon)
    intersections = 0

    dx2 = point[0] - polygon[0][0]
    dy2 = point[1] - polygon[0][1]
    jj = 1

    while jj < length:
        dx = dx2
        dy = dy2
        dx2 = point[0] - polygon[jj][0]
        dy2 = point[1] - polygon[jj][1]

        F = (dx - dx2) * dy - dx * (dy - dy2)
        if 0.0 == F and dx * dx2 <= 0 and dy * dy2 <= 0:
            return True

        if (dy >= 0 and dy2 < 0) or (dy2 >= 0 and dy < 0):
            if F > 0:
                intersections += 1
            elif F < 0:
                intersections -= 1

        jj += 1

    return intersections == 0


def get_clip_feature(gdf: gpd.GeoDataFrame) -> np.ndarray:
    """Creates a slightly larger (200m buffer) simplified geometry from the
    input geometry in the form of a numpy array with coordinates.

    :param gdf: a geodataframe containing a reservoir geometry.
    :type gdf: gpd.GeoDataFrame
    :return: a polygon as an array of points
    :rtype: np.ndarray
    """

    geoseries = gdf.loc[:, "geometry"]
    proj_crs = geoseries.estimate_utm_crs()
    gdf = gdf.to_crs(proj_crs)
    gdf.loc[0, "geometry"] = gdf.loc[0, "geometry"].buffer(200).simplify(50)
    gdf = gdf.to_crs(4326)
    geom_array = np.array(gdf.loc[0, "geometry"].exterior.coords)
    return geom_array


def filter_icesat2_data(df: pd.DataFrame, clip_geom: np.array) -> pd.DataFrame:
    """Filters a dataframe containing icesat2 data by calling
    points_in_polygon_parallel function to check if the icesat2 points are within
    a given clip geometry

    :param df: dataframe containing icesat2 points
    :type df: pd.DataFrame
    :param clip_geom: an array of points representing a polygon
    :type clip_geom: np.array
    :return: a filtered dataframe with points that are within in the clip geometry
    :rtype: pd.DataFrame
    """
    coords = np.array(list(zip(df.lon, df.lat))).astype(np.float32)
    bool_array = points_in_polygon_parallel(coords, clip_geom)
    return df[bool_array]


def process_icesat2_for_GEE(df: pd.DataFrame, icesat2_product: str) -> pd.DataFrame:
    """Processes a dataframe containing icesat2 points so that the resulting dataframe
    is ready for uploading to Google Earth Engine

    :param df: dataframe containing icesat2 points
    :type df: pd.DataFrame
    :return: A dataframe with renamed columns and encoded series data
    :rtype: pd.DataFrame
    """
    if icesat2_product == "atl03":
        df.series = df.series.map(
            {"High": 0, "Medium": 1, "Low": 2, "Buffer": 3, "Noise": 4}
        )
    df.date = pd.to_datetime(df.date).values.astype(np.int64) // 10**6

    df = df.rename(
        columns={
            "lon": "longitude",
            "lat": "latitude",
            "date": "system:time_start",
        }
    )
    return df


def get_icesat2_data(
    aoi: gpd.GeoDataFrame,
    clip_geom: bool = True,
    icesat2_product: str = "atl03",
    series_included: list = ["Medium", "High"],
) -> pd.DataFrame:
    bounding_box = get_bounding_box(aoi, icesat2_product)

    df_concat = pd.DataFrame()
    if clip_geom:
        clip_feature = get_clip_feature(aoi)

    for bounds in bounding_box:
        track_ids = get_track_ids(bounds)
        overpasses = get_overpasses(track_ids)

        for track_date, track_id in overpasses:
            # This function will request the 6 beams data using OpenAltimetry's API
            photon_data = get_icesat2_data_from_OA_api(
                icesat2_product=icesat2_product,
                boundingbox=bounds,
                track_date=track_date,
                track_id=track_id,
                series_included=series_included,
            )

            if icesat2_product == "atl03":
                rows = parse_atl03(photon_data, track_id, track_date)

            elif icesat2_product == "atl08":
                rows = parse_atl08(photon_data, track_id, track_date)

            if rows:
                print(f"downloaded data for date {track_date} and track id {track_id}")

                df = pd.DataFrame(rows)
                if clip_geom:
                    df_filtered = filter_icesat2_data(df, clip_feature)
                    print(len(df_filtered) == len(df))
                    df = df_filtered

                if df.empty:
                    print("no points within reservoir convex hull")
                    continue

                df = process_icesat2_for_GEE(df, icesat2_product)

                df_concat = pd.concat([df_concat, df])
    if df_concat.empty:
        print("No icesat2 data found for given aoi")
    return df_concat


def boundingbox_to_gdf(
    bbox: list, id: int, flood_date: str, crs: int = 4326
) -> gpd.GeoDataFrame:
    geom = box(*bbox)

    return gpd.GeoDataFrame(
        data={
            "id": [
                id,
            ],
            "flood_date": [flood_date],
        },
        geometry=[geom],
        crs=crs,
    )
