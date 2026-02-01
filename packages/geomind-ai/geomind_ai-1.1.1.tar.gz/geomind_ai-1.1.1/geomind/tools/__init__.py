"""
GeoMind Tools - Functions available to the AI agent.

This module contains all the tools that the agent can call:
- Geocoding: Convert place names to coordinates
- STAC Search: Query the Sentinel-2 catalog
- Processing: Load and process imagery data
"""

from .geocoding import geocode_location, get_bbox_from_location
from .stac_search import search_imagery, get_item_details, list_recent_imagery
from .processing import (
    create_rgb_composite,
    calculate_ndvi,
    get_band_statistics,
)

__all__ = [
    "geocode_location",
    "get_bbox_from_location",
    "search_imagery",
    "get_item_details",
    "list_recent_imagery",
    "create_rgb_composite",
    "calculate_ndvi",
    "get_band_statistics",
]
