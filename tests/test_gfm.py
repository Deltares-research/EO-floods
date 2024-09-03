from dotenv import load_dotenv
import os
import logging
import re

from ipyleaflet import Map
import pytest
from EO_Floods.providers import GFM
from EO_Floods.providers.GFM.auth import authenticate_gfm, _get_credentials_from_env

load_dotenv()


@pytest.mark.integration
def test_GFM(caplog, mocker):
    caplog.set_level(logging.INFO)

    gfm = GFM(
        start_date="2022-10-01",
        end_date="2022-10-15",
        geometry=[67.740187, 27.712453, 68.104933, 28.000935],
        email=os.getenv("GFM_EMAIL"),
        pwd=os.getenv("GFM_PWD"),
    )
    # Test init
    assert "Successfully authenticated to the GFM API\n" in caplog.text
    assert "Successfully uploaded geometry to GFM server" in caplog.text
    assert "Retrieving GFM product information" in caplog.text
    assert len(gfm.products) == 5
    assert gfm.user["client_id"] == "iiq9MAfBmxgYynhpxFwi78J5"

    # Test available_data
    dates = [product["product_time"] for product in gfm.products]
    gfm.available_data()
    assert f"For the following dates there is GFM data: {dates}" in caplog.text

    # Test select_data
    gfm.select_data(dates=dates[:2])
    assert len(gfm.products) == 2

    # Test view_data
    wms_map = gfm.view_data()
    assert isinstance(wms_map, Map)

    # Test export_data
    mock_get_request = mocker.patch("requests.get")
    mock_request_response = mocker.Mock(status_code=200, json=lambda: {"link": "mock_link"})
    mock_get_request.return_value = mock_request_response
    gfm.export_data()
    for product in gfm.products:
        assert f"Image: {product['product_time']}, download link: {{'link': 'mock_link'}}" in caplog.text

    with pytest.raises(ValueError, match="dates should be a list of dates, not <class 'str'>"):
        gfm.select_data(dates="03-04-1995")
    
    with pytest.raises(
        ValueError, match="No data found for given date\(s\): 03-04-1995"
    ):
        gfm.select_data(dates=["03-04-1995"])
    

    

def test_GFM_auth(mocker, caplog):
    mock_post_request = mocker.patch("requests.post")
    mock_response = mocker.Mock(status_code=200, json=lambda: {"test": "data"})
    mock_post_request.return_value = mock_response
    response = authenticate_gfm(email=os.getenv("GFM_EMAIL"), pwd=os.getenv("GFM_PWD"))
    assert "Successfully authenticated to the GFM API\n" in caplog.text
    assert isinstance(response, dict)

    response = authenticate_gfm(from_env=True)
    assert "Successfully authenticated to the GFM API\n" in caplog.text
    assert isinstance(response, dict)

    mock_response.status_code = 400
    authenticate_gfm(email=os.getenv("GFM_EMAIL"), pwd=os.getenv("GFM_PWD"))
    assert "Incorrect email or password, please try again\n" in caplog.text


def test_GFM_auth_get_credentials_from_env(mocker):
    email,pwd = _get_credentials_from_env()
    assert email == os.getenv("GFM_EMAIL")
    mock_getenv = mocker.patch("os.getenv")
    mock_getenv.return_value = None
    with pytest.raises(ValueError, match=re.escape("Environment variables ['GFM_EMAIL', 'GFM_PWD'] not set.")):
        _get_credentials_from_env()