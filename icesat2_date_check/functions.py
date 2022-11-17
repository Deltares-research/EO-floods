import requests
from datetime import datetime, timedelta

from retry import retry
import pandas as pd



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


def get_icesat2_data_from_OA_api(icesat2_product: str, boundingbox: list, track_date: str, track_id: str, series_included= ["Medium", "High"]) -> dict :
    
    series_included = "".join(["photonConfidence[]="+series.lower() for series in series_included])
    minx, miny, maxx, maxy = boundingbox
    OA_API_URL = (
        "https://openaltimetry.org/data/api/icesat2/{}?"
        "&minx={}&miny={}&maxx={}&maxy={}&date={}&trackId={}&{}"
        "&beamName=gt3r&beamName=gt3l&beamName=gt2r&beamName=gt2l&beamName=gt1r&beamName=gt1l".format(
            icesat2_product, minx, miny, maxx, maxy, track_date, track_id,series_included 
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



def expand_dates(dates):
    expanded_dates =[]
    for date in dates:
        date_1 = datetime.strptime(date, "%Y-%m-%d")
        date_0 = date_1 - timedelta(days=1)
        date_2 = date_1 + timedelta(days=1)
        expanded_dates.append(date_0)
        expanded_dates.append(date_1)
        expanded_dates.append(date_2)
    expanded_dates = list(set([datetime.strftime(date, "%Y-%m-%d") for date in expanded_dates]))
    return expanded_dates



def rewrite_dates(dates):
   return [datetime.strftime(datetime.strptime(date,"%d-%m-%Y"), "%Y-%m-%d") for date in dates]
    

def date_checker(aoi: list, dates: list):
    dates = rewrite_dates(dates)
    

    track_ids =  get_track_ids(aoi)
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
            data = get_icesat2_data_from_OA_api("atl08", aoi, track_date=date, track_id=trackid)
        
            rows = parse_atl08(data, track_id=trackid, track_date=date)
            if rows:
                print(f"icesat2 data found for {date}")
                df_rows = pd.DataFrame(rows)

                df = pd.concat([df, df_rows])
                df.drop_duplicates(inplace=True)
                
        return df
    else:
        print("no icesat2 data found for these dates")

    

    








