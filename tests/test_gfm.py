from EO_Floods.providers import GFM
from EO_Floods.providers.GFM.auth import GFM_authenticate
from dotenv import load_dotenv
import os
import logging
import pytest

load_dotenv()


@pytest.mark.integration
def test_GFM(caplog, capsys, mocker):
    caplog.set_level(logging.INFO)

    gfm = GFM(
        start_date="2022-10-01",
        end_date="2022-10-15",
        geometry=[67.740187, 27.712453, 68.104933, 28.000935],
        email=os.getenv("GFM_EMAIL"),
        pwd=os.getenv("GFM_PWD"),
    )
    # Test init
    captured = capsys.readouterr()
    assert "Successfully authenticated to the GFM API\n" in captured.out
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

    with pytest.raises(
        ValueError, match="No data found for given date\(s\): 03-04-1995"
    ):
        gfm.select_data(dates=["03-04-1995"])


def test_GFM_auth(mocker, capsys):
    mock_post_request = mocker.patch("requests.post")
    mock_response = mocker.Mock(status_code=200, json=lambda: {"test": "data"})
    mock_post_request.return_value = mock_response
    response = GFM_authenticate(email=os.getenv("GFM_EMAIL"), pwd=os.getenv("GFM_PWD"))
    captured = capsys.readouterr()
    assert "Successfully authenticated to the GFM API\n" in captured.out
    assert isinstance(response, dict)

    mock_response.status_code = 400
    GFM_authenticate(email=os.getenv("GFM_EMAIL"), pwd=os.getenv("GFM_PWD"))
    captured = capsys.readouterr()
    assert "Incorrect email or password, please try again\n" in captured.out
