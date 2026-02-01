"""
STAC API search tools for querying Sentinel-2 imagery.

Uses the EOPF STAC API at https://stac.core.eopf.eodc.eu
"""

from typing import Optional, List
from datetime import datetime, timedelta
from pystac_client import Client

from ..config import (
    STAC_API_URL,
    STAC_COLLECTION,
    DEFAULT_MAX_CLOUD_COVER,
    DEFAULT_MAX_ITEMS,
)


def _get_stac_client() -> Client:
    """Get a STAC API client instance."""
    return Client.open(STAC_API_URL)


def _format_item(item) -> dict:
    """Format a STAC item into a simplified dictionary."""
    props = item.properties

    # Extract individual band assets for direct access
    assets = {}
    for key, asset in item.assets.items():
        if key in ["SR_10m", "SR_20m", "SR_60m", "TCI_10m", "product"]:
            assets[key] = {
                "title": asset.title,
                "href": asset.href,
                "type": asset.media_type,
            }
        # Include individual 10m band assets for direct access
        elif key in ["B02_10m", "B03_10m", "B04_10m", "B08_10m"]:
            assets[key] = {
                "title": asset.title,
                "href": asset.href,
                "type": asset.media_type,
                "band": key.split("_")[0].lower(),  # Extract band name (b02, b03, b04, b08)
            }

    return {
        "id": item.id,
        "datetime": props.get("datetime"),
        "cloud_cover": props.get("eo:cloud_cover"),
        "platform": props.get("platform"),
        "bbox": item.bbox,
        "geometry": item.geometry,
        "assets": assets,
        "stac_url": f"{STAC_API_URL}/collections/{STAC_COLLECTION}/items/{item.id}",
    }


def search_imagery(
    bbox: Optional[List[float]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_cloud_cover: Optional[float] = None,
    max_items: Optional[int] = None,
) -> dict:
    """
    Search for Sentinel-2 L2A imagery in the EOPF STAC catalog.

    Args:
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        max_cloud_cover: Maximum cloud cover percentage (0-100)
        max_items: Maximum number of items to return

    Returns:
        Dictionary with search results including items found

    Example:
        >>> search_imagery(
        ...     bbox=[-74.0, 40.7, -73.9, 40.8],
        ...     start_date="2024-12-01",
        ...     end_date="2024-12-20",
        ...     max_cloud_cover=20
        ... )
    """
    if max_cloud_cover is None:
        max_cloud_cover = DEFAULT_MAX_CLOUD_COVER
    if max_items is None:
        max_items = DEFAULT_MAX_ITEMS

    # Build datetime string
    datetime_str = None
    if start_date or end_date:
        start = start_date or "2015-01-01"
        end = end_date or datetime.now().strftime("%Y-%m-%d")
        datetime_str = f"{start}/{end}"

    try:
        client = _get_stac_client()

        # Build search parameters
        search_params = {
            "collections": [STAC_COLLECTION],
            "max_items": max_items,
        }

        if bbox:
            search_params["bbox"] = bbox

        if datetime_str:
            search_params["datetime"] = datetime_str

        # Execute search
        search = client.search(**search_params)
        items = list(search.items())

        # Filter by cloud cover (post-filter since API may not support query param)
        filtered_items = [
            item
            for item in items
            if item.properties.get("eo:cloud_cover", 100) <= max_cloud_cover
        ]

        # Sort by date (newest first)
        filtered_items.sort(
            key=lambda x: x.properties.get("datetime", ""), reverse=True
        )

        # Format results
        formatted_items = [_format_item(item) for item in filtered_items]

        return {
            "success": True,
            "total_found": len(items),
            "filtered_count": len(filtered_items),
            "items": formatted_items,
            "search_params": {
                "bbox": bbox,
                "datetime": datetime_str,
                "max_cloud_cover": max_cloud_cover,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "items": [],
        }


def get_item_details(item_id: str) -> dict:
    """
    Get detailed information about a specific STAC item.

    Args:
        item_id: The STAC item ID (e.g., "S2B_MSIL2A_20251218T110359_...")

    Returns:
        Dictionary with full item details including all assets
    """
    try:
        client = _get_stac_client()
        collection = client.get_collection(STAC_COLLECTION)

        # Get the item
        item_url = f"{STAC_API_URL}/collections/{STAC_COLLECTION}/items/{item_id}"

        import requests

        response = requests.get(item_url)
        response.raise_for_status()
        item_data = response.json()

        return {
            "success": True,
            "item": item_data,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def list_recent_imagery(
    location_name: Optional[str] = None,
    days: int = 7,
    max_cloud_cover: Optional[float] = None,
    max_items: Optional[int] = None,
) -> dict:
    """
    List recent Sentinel-2 imagery, optionally for a specific location.

    This is a convenience function that combines geocoding and search.

    Args:
        location_name: Optional place name to search around
        days: Number of days to look back (default: 7)
        max_cloud_cover: Maximum cloud cover percentage
        max_items: Maximum items to return

    Returns:
        Dictionary with recent imagery items
    """
    from .geocoding import get_bbox_from_location

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Get bbox if location provided
    bbox = None
    location_info = None

    if location_name:
        bbox_result = get_bbox_from_location(location_name)
        if bbox_result["success"]:
            bbox = bbox_result["bbox"]
            location_info = {
                "name": location_name,
                "center": bbox_result["center"],
                "address": bbox_result["address"],
            }
        else:
            return {
                "success": False,
                "error": f"Could not geocode location: {location_name}",
            }

    # Search for imagery
    result = search_imagery(
        bbox=bbox,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        max_cloud_cover=max_cloud_cover,
        max_items=max_items,
    )

    if location_info:
        result["location"] = location_info

    return result
