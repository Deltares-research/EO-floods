"""An easy to use interface for deriving flood maps from earth observation data."""

from dotenv import load_dotenv

from eo_floods.floodmap import FloodMap

load_dotenv()

__version__ = "2023.12"
__all__ = ["FloodMap"]
