import os
import logging

import ee

log = logging.getLogger(__name__)


def ee_initialize(token_name="EARTHENGINE_TOKE"):
    """Authenticates Earth Engine and intializes an Earth Engine session."""
    if ee.data._credentials is None:
        try:
            ee_token = os.environ.get(token_name)
            if ee_token is not None:
                credentials_file_path = os.path.expanduser("~/.config/earthengine/")
                if not os.path.exists(credentials_file_path):
                    credential = '{"refresh_token":"%s"}' % ee_token
                    os.makedirs(credentials_file_path, exist_ok=True)
                    with open(credentials_file_path + "credentials", "w") as file:
                        file.write(credential)
            ee.Initialize()
        except Exception:
            ee.Authenticate()
            ee.Initialize()
    ee.Initialize()
