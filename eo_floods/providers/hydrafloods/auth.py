"""Function for authenticatinh to earth engine with environment variables."""

import logging
import os
from pathlib import Path

import ee

log = logging.getLogger(__name__)


def ee_initialize(token_name: str = "EARTHENGINE_TOKEN") -> None:  # noqa: S107
    """Authenticate Earth Engine and intializes an Earth Engine session."""
    if ee.data._credentials is None:  # noqa: SLF001
        try:
            ee_token = os.environ.get(token_name)
            if ee_token is not None:
                credentials_file_path = Path("~/.config/earthengine/").expanduser()
                if not credentials_file_path.exists():
                    credential = '{"refresh_token":"{ee_token}"}'
                    credentials_file_path.mkdir(parents=True)
                    with credentials_file_path.joinpath("credentials").open("w") as file:
                        file.write(credential)
            ee.Initialize()
        except Exception:  # noqa: BLE001
            ee.Authenticate()
    ee.Initialize(project=os.environ.get("EARTH_ENGINE_PROJECT"))
