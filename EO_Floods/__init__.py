"""An easy to use interface for deriving flood maps from earth observation data."""  # noqa: N999

from dotenv import load_dotenv

from EO_Floods.floodmap import FloodMap

load_dotenv()

__version__ = "2023.12"
__all__ = ["FloodMap"]
