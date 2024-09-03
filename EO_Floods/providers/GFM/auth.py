"""Authentication module for GFM provider."""

from __future__ import annotations

import getpass
import logging
import os

import requests
from requests import Request

log = logging.getLogger(__name__)


def authenticate_gfm(email: str | None = None, pwd: str | None = None, *, from_env: bool = False) -> dict:
    """Authenticate to the GFM server.

    Parameters
    ----------
    email : str, optional
        GFM account email, by default None
    pwd : str, optional
        GFM account password, by default None
    from_env : bool, optional
        bool option to use environment viarables. If set to True this function will look for 'GFM_EMAIL' and 'GFM_PWD`.

    Returns
    -------
    dict
        returns user information

    Raises
    ------
    r.raise_for_status
        _description_

    """
    from_input_prompt = False
    if not email and not pwd and not from_env:
        log.info(
            "To authenticate to the GFM API please enter your email and your password in the following prompts",
        )
        email = input(prompt="Enter your email")
        pwd = getpass.getpass(prompt="Enter your password")
        from_input_prompt = True
    elif not email and not pwd and from_env:
        email, pwd = _get_credentials_from_env()
    url = "https://api.gfm.eodc.eu/v2/auth/login"
    r = requests.post(url=url, json={"email": email, "password": pwd}, timeout=120)
    if r.status_code == 200:  # noqa: PLR2004
        log.info("Successfully authenticated to the GFM API")
        return r.json()
    if r.status_code == 400:  # noqa: PLR2004
        log.info("Incorrect email or password, please try again")
        if from_input_prompt:
            return authenticate_gfm(email, pwd)
    else:
        raise r.raise_for_status()
    return None


def _get_credentials_from_env() -> str:
    email = os.getenv("GFM_EMAIL")
    pwd = os.getenv("GFM_PWD")
    if not email or not pwd:
        err_msg = "Environment variables ['GFM_EMAIL', 'GFM_PWD'] not set."
        raise ValueError(err_msg)
    return email, pwd


class BearerAuth(requests.auth.AuthBase):
    """Wrapper class for bearer auth tokens."""

    def __init__(self, token: str) -> None:
        """Instantiate BearerAuth object."""
        self.token = token

    def __call__(self, r: Request) -> Request:
        """__call__ overwrite to add bearer auth token to header."""
        r.headers["authorization"] = "Bearer " + self.token
        return r
