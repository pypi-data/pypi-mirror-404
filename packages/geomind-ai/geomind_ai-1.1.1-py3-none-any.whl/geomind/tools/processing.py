"""
Image processing tools for Sentinel-2 data.

Handles loading Zarr data, applying corrections, and creating visualizations.
"""

from typing import Optional, List, Tuple
from pathlib import Path
import numpy as np

# Use non-interactive backend BEFORE any other matplotlib imports
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..config import (
    REFLECTANCE_SCALE,
    REFLECTANCE_OFFSET,
    RGB_BANDS,
    OUTPUT_DIR,
)


def _apply_scale_offset(
    data: np.ndarray,
    scale: float = REFLECTANCE_SCALE,
    offset: float = REFLECTANCE_OFFSET,
    nodata: int = 0,
) -> np.ndarray:
    """
    Apply scale and offset to convert DN to surface reflectance.

    Formula: reflectance = (DN * scale) + offset

    Args:
        data: Raw digital number values
        scale: Scale factor (default: 0.0001)
        offset: Offset value (default: -0.1)
        nodata: NoData value to mask (default: 0)

    Returns:
        Surface reflectance values
    """
    # Create mask for nodata
    mask = data == nodata

    # Apply transformation
    result = (data.astype(np.float32) * scale) + offset

    # Set nodata pixels to NaN
    result[mask] = np.nan

    return result


def _normalize_for_display(
    data: np.ndarray,
    percentile_low: float = 2,
    percentile_high: float = 98,
) -> np.ndarray:
    """
    Normalize data to 0-1 range for display using percentile stretch.

    Args:
        data: Input array
        percentile_low: Lower percentile for clipping
        percentile_high: Upper percentile for clipping

    Returns:
        Normalized array in 0-1 range
    """
    # Get valid (non-NaN) values
    valid = data[~np.isnan(data)]

    if len(valid) == 0:
        return np.zeros_like(data)

    # Calculate percentiles
    low = np.percentile(valid, percentile_low)
    high = np.percentile(valid, percentile_high)

    # Normalize
    if high > low:
        result = (data - low) / (high - low)
    else:
        result = np.zeros_like(data)

    # Clip to 0-1
    result = np.clip(result, 0, 1)

    # Set NaN to 0 for display
    result = np.nan_to_num(result, nan=0)

    return result


def create_rgb_composite(
    zarr_url: str,
    output_path: Optional[str] = None,
    subset_size: Optional[int] = 1000,
) -> dict:
    """
    Create an RGB composite image from Sentinel-2 10m bands.

    Uses B04 (Red), B03 (Green), B02 (Blue) bands.

    Args:
        zarr_url: URL to the SR_10m Zarr asset or individual band asset URL
        output_path: Optional path to save the image
        subset_size: Size to subset the image (for faster processing)

    Returns:
        Dictionary with path to saved image and metadata
    """
    try:
        import xarray as xr
        import zarr

        # Determine if this is a band-specific URL or base SR_10m URL
        # Band-specific URLs end with /b02, /b03, /b04, etc.
        # Base SR_10m URLs end with /r10m
        is_band_url = zarr_url.rstrip('/').split('/')[-1].startswith('b')
        
        if is_band_url:
            # Individual band URL provided - need to construct URLs for each band
            base_url = '/'.join(zarr_url.rstrip('/').split('/')[:-1])
            red = np.array(zarr.open(f"{base_url}/b04", mode="r"))
            green = np.array(zarr.open(f"{base_url}/b03", mode="r"))
            blue = np.array(zarr.open(f"{base_url}/b02", mode="r"))
        else:
            # Base SR_10m URL - bands are subdirectories
            base_url = zarr_url.rstrip('/')
            red = np.array(zarr.open(f"{base_url}/b04", mode="r"))
            green = np.array(zarr.open(f"{base_url}/b03", mode="r"))
            blue = np.array(zarr.open(f"{base_url}/b02", mode="r"))

        # Subset if requested (for faster processing)
        if subset_size and red.shape[0] > subset_size:
            # Take center subset
            h, w = red.shape
            start_h = (h - subset_size) // 2
            start_w = (w - subset_size) // 2
            red = red[start_h : start_h + subset_size, start_w : start_w + subset_size]
            green = green[
                start_h : start_h + subset_size, start_w : start_w + subset_size
            ]
            blue = blue[
                start_h : start_h + subset_size, start_w : start_w + subset_size
            ]

        # Apply scale and offset
        red = _apply_scale_offset(red)
        green = _apply_scale_offset(green)
        blue = _apply_scale_offset(blue)

        # Normalize for display
        red = _normalize_for_display(red)
        green = _normalize_for_display(green)
        blue = _normalize_for_display(blue)

        # Stack into RGB
        rgb = np.dstack([red, green, blue])

        # Generate output path
        if output_path is None:
            output_path = OUTPUT_DIR / f"rgb_composite_{np.random.randint(10000)}.png"
        else:
            output_path = Path(output_path)

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(rgb)
        ax.set_title("Sentinel-2 RGB Composite (B4/B3/B2)")
        ax.axis("off")

        # Save
        plt.savefig(output_path, dpi=150, bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        plt.close('all')  # Ensure all figures are closed

        return {
            "success": True,
            "output_path": str(output_path),
            "image_size": rgb.shape[:2],
            "bands_used": ["B04 (Red)", "B03 (Green)", "B02 (Blue)"],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def calculate_ndvi(
    zarr_url: str,
    output_path: Optional[str] = None,
    subset_size: Optional[int] = 1000,
) -> dict:
    """
    Calculate NDVI (Normalized Difference Vegetation Index) from Sentinel-2 data.

    NDVI = (NIR - Red) / (NIR + Red)
    Uses B08 (NIR) and B04 (Red) bands.

    Args:
        zarr_url: URL to the SR_10m Zarr asset or individual band asset URL
        output_path: Optional path to save the NDVI image
        subset_size: Size to subset the image

    Returns:
        Dictionary with NDVI statistics and output path
    """
    try:
        import zarr
        from matplotlib.colors import LinearSegmentedColormap

        # Determine if this is a band-specific URL or base SR_10m URL
        is_band_url = zarr_url.rstrip('/').split('/')[-1].startswith('b')
        
        if is_band_url:
            # Individual band URL provided
            base_url = '/'.join(zarr_url.rstrip('/').split('/')[:-1])
            nir = np.array(zarr.open(f"{base_url}/b08", mode="r"))
            red = np.array(zarr.open(f"{base_url}/b04", mode="r"))
        else:
            # Base SR_10m URL
            base_url = zarr_url.rstrip('/')
            nir = np.array(zarr.open(f"{base_url}/b08", mode="r"))
            red = np.array(zarr.open(f"{base_url}/b04", mode="r"))

        # Subset if requested
        if subset_size and nir.shape[0] > subset_size:
            h, w = nir.shape
            start_h = (h - subset_size) // 2
            start_w = (w - subset_size) // 2
            nir = nir[start_h : start_h + subset_size, start_w : start_w + subset_size]
            red = red[start_h : start_h + subset_size, start_w : start_w + subset_size]

        # Apply scale and offset
        nir = _apply_scale_offset(nir)
        red = _apply_scale_offset(red)

        # Calculate NDVI
        # Avoid division by zero
        denominator = nir + red
        denominator[denominator == 0] = np.nan

        ndvi = (nir - red) / denominator

        # NDVI statistics
        valid_ndvi = ndvi[~np.isnan(ndvi)]
        stats = {
            "min": float(np.min(valid_ndvi)) if len(valid_ndvi) > 0 else None,
            "max": float(np.max(valid_ndvi)) if len(valid_ndvi) > 0 else None,
            "mean": float(np.mean(valid_ndvi)) if len(valid_ndvi) > 0 else None,
            "std": float(np.std(valid_ndvi)) if len(valid_ndvi) > 0 else None,
        }

        # Generate output path
        if output_path is None:
            output_path = OUTPUT_DIR / f"ndvi_{np.random.randint(10000)}.png"
        else:
            output_path = Path(output_path)

        # Create NDVI colormap (brown -> yellow -> green)
        colors = ["#8B4513", "#D2691E", "#FFD700", "#ADFF2F", "#228B22", "#006400"]
        ndvi_cmap = LinearSegmentedColormap.from_list("ndvi", colors)

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 10))
        im = ax.imshow(ndvi, cmap=ndvi_cmap, vmin=-1, vmax=1)
        ax.set_title("NDVI - Normalized Difference Vegetation Index")
        ax.axis("off")

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label("NDVI")

        # Save
        plt.savefig(output_path, dpi=150, bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        plt.close('all')  # Ensure all figures are closed

        return {
            "success": True,
            "output_path": str(output_path),
            "statistics": stats,
            "interpretation": _interpret_ndvi(stats["mean"]) if stats["mean"] else None,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _interpret_ndvi(mean_ndvi: float) -> str:
    """Provide interpretation of mean NDVI value."""
    if mean_ndvi < 0:
        return "Water or bare surfaces dominant"
    elif mean_ndvi < 0.1:
        return "Bare soil or built-up areas"
    elif mean_ndvi < 0.2:
        return "Sparse vegetation or stressed plants"
    elif mean_ndvi < 0.4:
        return "Moderate vegetation"
    elif mean_ndvi < 0.6:
        return "Dense vegetation"
    else:
        return "Very dense/healthy vegetation"


def get_band_statistics(
    zarr_url: str,
    bands: Optional[List[str]] = None,
) -> dict:
    """
    Get statistics for specified bands from a Sentinel-2 Zarr asset.

    Args:
        zarr_url: URL to the Zarr asset (e.g., SR_10m)
        bands: List of band names (default: all available)

    Returns:
        Dictionary with statistics for each band
    """
    try:
        import zarr

        store = zarr.open(zarr_url, mode="r")

        # Get available bands if not specified
        if bands is None:
            bands = [key for key in store.keys() if key.startswith("b")]

        results = {}

        for band in bands:
            if band not in store:
                results[band] = {"error": "Band not found"}
                continue

            data = np.array(store[band])

            # Apply scale/offset
            data = _apply_scale_offset(data)
            valid = data[~np.isnan(data)]

            if len(valid) > 0:
                results[band] = {
                    "min": float(np.min(valid)),
                    "max": float(np.max(valid)),
                    "mean": float(np.mean(valid)),
                    "std": float(np.std(valid)),
                    "shape": data.shape,
                }
            else:
                results[band] = {"error": "No valid data"}

        return {
            "success": True,
            "band_statistics": results,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
