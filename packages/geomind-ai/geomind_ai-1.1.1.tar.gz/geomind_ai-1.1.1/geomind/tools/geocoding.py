"""
Geocoding tools for converting place names to coordinates.

Uses OpenStreetMap's Nominatim service via geopy.
"""

from typing import Optional
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from ..config import GEOCODER_USER_AGENT, DEFAULT_BUFFER_KM


def geocode_location(place_name: str) -> dict:
    """
    Convert a place name to geographic coordinates.

    Args:
        place_name: Name of the location (e.g., "New York", "Paris, France")

    Returns:
        Dictionary with latitude, longitude, and full address

    Example:
        >>> geocode_location("Central Park, New York")
        {'latitude': 40.7828, 'longitude': -73.9653, 'address': '...'}
    """
    geolocator = Nominatim(user_agent=GEOCODER_USER_AGENT, timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    location = geocode(place_name)

    if location is None:
        return {
            "success": False,
            "error": f"Could not find location: {place_name}",
            "latitude": None,
            "longitude": None,
            "address": None,
        }

    return {
        "success": True,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "address": location.address,
    }


def get_bbox_from_location(place_name: str, buffer_km: Optional[float] = None) -> dict:
    """
    Convert a place name to a bounding box suitable for STAC queries.

    Creates a square bounding box centered on the location with the
    specified buffer distance.

    Args:
        place_name: Name of the location (e.g., "San Francisco")
        buffer_km: Buffer distance in kilometers (default: 10km)

    Returns:
        Dictionary with bbox [min_lon, min_lat, max_lon, max_lat] and center point

    Example:
        >>> get_bbox_from_location("London", buffer_km=5)
        {'bbox': [-0.17, 51.46, -0.08, 51.55], 'center': {...}}
    """
    if buffer_km is None:
        buffer_km = DEFAULT_BUFFER_KM

    # Get coordinates
    location_result = geocode_location(place_name)

    if not location_result["success"]:
        return {
            "success": False,
            "error": location_result["error"],
            "bbox": None,
        }

    lat = location_result["latitude"]
    lon = location_result["longitude"]

    # Calculate approximate degree offset
    # 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 * cos(latitude) km
    import math

    lat_offset = buffer_km / 111.0
    lon_offset = buffer_km / (111.0 * math.cos(math.radians(lat)))

    bbox = [
        lon - lon_offset,  # min_lon (west)
        lat - lat_offset,  # min_lat (south)
        lon + lon_offset,  # max_lon (east)
        lat + lat_offset,  # max_lat (north)
    ]

    return {
        "success": True,
        "bbox": bbox,
        "center": {
            "latitude": lat,
            "longitude": lon,
        },
        "address": location_result["address"],
        "buffer_km": buffer_km,
    }
