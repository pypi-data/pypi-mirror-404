"""
Configuration settings for GeoMind agent.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# STAC API Configuration
STAC_API_URL = "https://stac.core.eopf.eodc.eu"
STAC_COLLECTION = "sentinel-2-l2a"

# Sentinel-2 Band Configuration
SENTINEL2_BANDS = {
    "B01": {"name": "Coastal aerosol", "wavelength": 0.443, "resolution": 60},
    "B02": {"name": "Blue", "wavelength": 0.490, "resolution": 10},
    "B03": {"name": "Green", "wavelength": 0.560, "resolution": 10},
    "B04": {"name": "Red", "wavelength": 0.665, "resolution": 10},
    "B05": {"name": "Red Edge 1", "wavelength": 0.704, "resolution": 20},
    "B06": {"name": "Red Edge 2", "wavelength": 0.740, "resolution": 20},
    "B07": {"name": "Red Edge 3", "wavelength": 0.783, "resolution": 20},
    "B08": {"name": "NIR", "wavelength": 0.842, "resolution": 10},
    "B8A": {"name": "NIR Narrow", "wavelength": 0.865, "resolution": 20},
    "B09": {"name": "Water Vapour", "wavelength": 0.945, "resolution": 60},
    "B11": {"name": "SWIR 1", "wavelength": 1.610, "resolution": 20},
    "B12": {"name": "SWIR 2", "wavelength": 2.190, "resolution": 20},
}

# Reflectance scale and offset (from STAC metadata)
REFLECTANCE_SCALE = 0.0001
REFLECTANCE_OFFSET = -0.1

# RGB Band Mapping
RGB_BANDS = {"red": "b04", "green": "b03", "blue": "b02"}

# Default search parameters
DEFAULT_MAX_CLOUD_COVER = 20  # percent
DEFAULT_BUFFER_KM = 10  # km buffer around point for bbox
DEFAULT_MAX_ITEMS = 10

# Output directory for saved images
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Geocoding configuration
GEOCODER_USER_AGENT = "geomind_agent_v0.1"

# OpenRouter API Configuration
# Get your free API key at: https://openrouter.ai/settings/keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")
