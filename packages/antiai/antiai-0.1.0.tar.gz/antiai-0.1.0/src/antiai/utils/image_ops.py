"""
Image operations and utilities.

This module provides helper functions for image manipulation,
validation, and conversion operations.
"""

from io import BytesIO
from pathlib import Path
from typing import Any, Tuple, Union

import numpy as np
from PIL import Image

from ..core.exceptions import ImageError, ImageTooLargeError, UnsupportedImageFormatError

# Constants
MAX_DIMENSION: int = 16384  # 16K pixels max per dimension
SUPPORTED_FORMATS: set[str] = {"PNG", "JPEG", "JPG", "WEBP", "BMP", "TIFF"}
SUPPORTED_MODES: set[str] = {"L", "RGB", "RGBA"}


def load_image(path: Union[str, Path]) -> Tuple[np.ndarray, Image.Image]:
    """
    Load image from file and convert to numpy array.

    Args:
        path: Path to image file

    Returns:
        Tuple of (numpy array, PIL Image)

    Raises:
        ImageError: If image cannot be loaded
        UnsupportedImageFormatError: If format is not supported
        ImageTooLargeError: If image exceeds maximum dimensions

    Example:
        >>> img_array, img_pil = load_image("photo.jpg")
        >>> img_array.shape
        (1080, 1920, 3)
    """
    path = Path(path)

    if not path.exists():
        raise ImageError(f"Image file not found: {path}")

    try:
        img = Image.open(path)
    except Exception as e:
        raise ImageError(f"Failed to open image: {e}") from e

    # Validate format
    if img.format not in SUPPORTED_FORMATS:
        raise UnsupportedImageFormatError(img.format or "unknown", list(SUPPORTED_FORMATS))

    # Validate dimensions
    width, height = img.size
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise ImageTooLargeError(width, height, MAX_DIMENSION)

    # Convert to supported mode
    if img.mode not in SUPPORTED_MODES:
        if img.mode in ("P", "PA"):
            img = img.convert("RGBA" if "transparency" in img.info else "RGB")
        elif img.mode in ("LA", "La"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

    # Convert to numpy array
    img_array = np.array(img)

    return img_array, img


def save_image(img_array: np.ndarray, path: Union[str, Path], format: str = "PNG") -> None:
    """
    Save numpy array as image file.

    Args:
        img_array: Numpy array with shape (H, W) or (H, W, C)
        path: Output file path
        format: Image format (PNG, JPEG, etc.)

    Raises:
        ImageError: If save fails
        UnsupportedImageFormatError: If format is not supported

    Example:
        >>> img = np.zeros((100, 100, 3), dtype=np.uint8)
        >>> save_image(img, "output.png")
    """
    format = format.upper()
    if format not in SUPPORTED_FORMATS:
        raise UnsupportedImageFormatError(format, list(SUPPORTED_FORMATS))

    try:
        img = Image.fromarray(img_array)
        img.save(path, format=format)
    except Exception as e:
        raise ImageError(f"Failed to save image: {e}") from e


def array_to_bytes(img_array: np.ndarray, format: str = "PNG", **kwargs: Any) -> bytes:
    """
    Convert numpy array to image bytes.

    Args:
        img_array: Image as numpy array
        format: Output format
        **kwargs: Additional arguments for PIL.Image.save()

    Returns:
        Image bytes in specified format

    Example:
        >>> img = np.zeros((100, 100, 3), dtype=np.uint8)
        >>> data = array_to_bytes(img, format="PNG")
        >>> len(data) > 0
        True
    """
    img = Image.fromarray(img_array)
    buffer = BytesIO()
    img.save(buffer, format=format, **kwargs)
    return buffer.getvalue()


def bytes_to_array(data: bytes) -> np.ndarray:
    """
    Convert image bytes to numpy array.

    Args:
        data: Image data as bytes

    Returns:
        Image as numpy array

    Raises:
        ImageError: If conversion fails

    Example:
        >>> # Assuming we have valid PNG bytes
        >>> img_array = bytes_to_array(png_bytes)
        >>> img_array.shape
        (100, 100, 3)
    """
    try:
        img = Image.open(BytesIO(data))
        return np.array(img)
    except Exception as e:
        raise ImageError(f"Failed to convert bytes to array: {e}") from e


def normalize_array(img_array: np.ndarray) -> np.ndarray:
    """
    Normalize image array to float32 [0, 1] range.

    Args:
        img_array: Image array (uint8 [0, 255])

    Returns:
        Normalized float32 array [0, 1]

    Example:
        >>> img = np.array([[[255, 0, 128]]], dtype=np.uint8)
        >>> normalized = normalize_array(img)
        >>> normalized[0, 0]
        array([1.  , 0.  , 0.50196078], dtype=float32)
    """
    return img_array.astype(np.float32) / 255.0


def denormalize_array(img_array: np.ndarray) -> np.ndarray:
    """
    Denormalize image array from [0, 1] to uint8 [0, 255].

    Args:
        img_array: Normalized float array [0, 1]

    Returns:
        Uint8 array [0, 255]

    Example:
        >>> img = np.array([[[1.0, 0.0, 0.5]]], dtype=np.float32)
        >>> denormalized = denormalize_array(img)
        >>> denormalized[0, 0]
        array([255,   0, 128], dtype=uint8)
    """
    return (np.clip(img_array, 0, 1) * 255).astype(np.uint8)


def rgb_to_grayscale(img_array: np.ndarray) -> np.ndarray:
    """
    Convert RGB image to grayscale using luminance formula.

    Uses ITU-R BT.601 luma coefficients: Y = 0.299R + 0.587G + 0.114B

    Args:
        img_array: RGB image array (H, W, 3)

    Returns:
        Grayscale image array (H, W)

    Example:
        >>> rgb = np.array([[[255, 0, 0]]], dtype=np.uint8)  # Red
        >>> gray = rgb_to_grayscale(rgb)
        >>> gray[0, 0]  # Approximately 76
        76
    """
    if img_array.ndim != 3 or img_array.shape[2] != 3:
        raise ValueError(f"Expected RGB image (H, W, 3), got shape {img_array.shape}")

    # ITU-R BT.601 coefficients
    weights = np.array([0.299, 0.587, 0.114], dtype=np.float32)

    if img_array.dtype == np.uint8:
        gray = np.dot(img_array.astype(np.float32), weights)
        return gray.astype(np.uint8)
    else:
        return np.dot(img_array, weights)


def calculate_psnr(original: np.ndarray, modified: np.ndarray) -> float:
    """
    Calculate Peak Signal-to-Noise Ratio between two images.

    Higher PSNR indicates more similarity. Values above 40 dB are
    generally considered imperceptible to human vision.

    Args:
        original: Original image array
        modified: Modified image array

    Returns:
        PSNR in decibels (dB)

    Raises:
        ValueError: If images have different shapes

    Example:
        >>> original = np.ones((100, 100, 3), dtype=np.uint8) * 128
        >>> modified = original.copy()
        >>> psnr = calculate_psnr(original, modified)
        >>> psnr
        inf
    """
    if original.shape != modified.shape:
        raise ValueError(f"Shape mismatch: original {original.shape}, modified {modified.shape}")

    mse = np.mean((original.astype(np.float64) - modified.astype(np.float64)) ** 2)

    if mse == 0:
        return float("inf")

    max_pixel = 255.0
    psnr = 10 * np.log10(max_pixel**2 / mse)

    return float(psnr)


def calculate_ssim_simple(original: np.ndarray, modified: np.ndarray) -> float:
    """
    Calculate simplified Structural Similarity Index.

    This is a simplified version. For production, consider using
    skimage.metrics.structural_similarity for full SSIM.

    Values closer to 1.0 indicate higher similarity.

    Args:
        original: Original image array
        modified: Modified image array

    Returns:
        SSIM value [0, 1]

    Raises:
        ValueError: If images have different shapes

    Example:
        >>> img1 = np.ones((100, 100), dtype=np.uint8) * 128
        >>> img2 = img1.copy()
        >>> ssim = calculate_ssim_simple(img1, img2)
        >>> ssim
        1.0
    """
    if original.shape != modified.shape:
        raise ValueError(f"Shape mismatch: original {original.shape}, modified {modified.shape}")

    # Convert to float64 for precision
    img1 = original.astype(np.float64)
    img2 = modified.astype(np.float64)

    # Constants to avoid division by zero
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    # Calculate means
    mu1 = img1.mean()
    mu2 = img2.mean()

    # Calculate variances and covariance
    sigma1_sq = ((img1 - mu1) ** 2).mean()
    sigma2_sq = ((img2 - mu2) ** 2).mean()
    sigma12 = ((img1 - mu1) * (img2 - mu2)).mean()

    # SSIM formula
    numerator = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)
    denominator = (mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2)

    ssim = numerator / denominator

    return float(np.clip(ssim, 0, 1))
