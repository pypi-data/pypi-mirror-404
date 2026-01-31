"""
Multispectral QR – RGB and palette decoders with robustness features.

Functions:
    decode_rgb(img, threshold_method, preprocess, calibration, method) -> list[str]
    decode_layers(img, num_layers, preprocess, calibration, method) -> list[str]
"""
from __future__ import annotations

from typing import List, Literal, Any

import numpy as np
import cv2
from PIL import Image


# Check if pyzbar is available for fallback decoding
try:
    from pyzbar import pyzbar as _pyzbar
    _PYZBAR_AVAILABLE = True
except ImportError:
    _pyzbar = None
    _PYZBAR_AVAILABLE = False


# Valid threshold methods
ThresholdMethod = Literal["global", "otsu", "adaptive_gaussian", "adaptive_mean"]

# Valid preprocessing options
PreprocessMethod = Literal["none", "blur", "denoise"]

# Valid decoding methods
DecodeMethod = Literal["threshold", "ml"]


def _apply_preprocessing(arr: np.ndarray, method: PreprocessMethod) -> np.ndarray:
    """Apply preprocessing to an image array."""
    if method == "none" or method is None:
        return arr
    elif method == "blur":
        # Gaussian blur to reduce noise
        return cv2.GaussianBlur(arr, (3, 3), 0)
    elif method == "denoise":
        # Non-local means denoising
        if len(arr.shape) == 3:
            return cv2.fastNlMeansDenoisingColored(arr, None, 10, 10, 7, 21)
        else:
            return cv2.fastNlMeansDenoising(arr, None, 10, 7, 21)
    else:
        return arr


def _apply_threshold(
    channel: np.ndarray,
    method: ThresholdMethod = "global",
) -> np.ndarray:
    """
    Apply thresholding to a single channel image.

    Args:
        channel: Grayscale image (H x W)
        method: Thresholding method to use

    Returns:
        Binary image (0 or 255)
    """
    if method == "global":
        # Simple global threshold at 128
        _, binary = cv2.threshold(channel, 128, 255, cv2.THRESH_BINARY_INV)
    elif method == "otsu":
        # Otsu's automatic threshold selection
        _, binary = cv2.threshold(channel, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    elif method == "adaptive_gaussian":
        # Adaptive threshold using Gaussian-weighted mean
        binary = cv2.adaptiveThreshold(
            channel, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
    elif method == "adaptive_mean":
        # Adaptive threshold using mean of neighborhood
        binary = cv2.adaptiveThreshold(
            channel, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
    else:
        raise ValueError(
            f"Invalid threshold_method: {method}. "
            f"Must be one of: global, otsu, adaptive_gaussian, adaptive_mean"
        )
    return binary


def _decode_single_layer(layer_img: np.ndarray) -> str | None:
    """
    Try to decode a monochrome QR layer (0/255 uint8).
    
    Uses OpenCV's QRCodeDetector as primary decoder, with pyzbar as fallback
    to handle edge cases where OpenCV fails on valid QR codes.
    
    Args:
        layer_img: Binary image with QR code (0=black, 255=white)
        
    Returns:
        Decoded text, or None if decoding fails.
    """
    # Try OpenCV first (faster)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(layer_img)
    if data:
        return data
    
    # Fallback to pyzbar if available (handles some edge cases OpenCV misses)
    if _PYZBAR_AVAILABLE:
        # pyzbar expects a PIL Image
        pil_img = Image.fromarray(layer_img)
        results = _pyzbar.decode(pil_img)
        if results:
            return results[0].data.decode('utf-8')
    
    return None


def decode_rgb(
    img: Image.Image,
    *,
    threshold_method: ThresholdMethod = "global",
    preprocess: PreprocessMethod | None = None,
    calibration: dict[str, Any] | None = None,
    method: DecodeMethod = "threshold",
) -> List[str]:
    """
    Split an RGB QR image into R, G, B layers, threshold each,
    and return a list of decoded strings (order: R, G, B).

    Args:
        img: PIL Image in RGB mode
        threshold_method: Thresholding algorithm to use:
            - "global": Simple threshold at 128 (default, fastest)
            - "otsu": Otsu's automatic threshold selection
            - "adaptive_gaussian": Adaptive threshold with Gaussian weights
            - "adaptive_mean": Adaptive threshold with mean of neighborhood
        preprocess: Optional preprocessing:
            - None or "none": No preprocessing
            - "blur": Gaussian blur to reduce noise
            - "denoise": Non-local means denoising
        calibration: Optional calibration data from compute_calibration()
        method: Decoding method to use:
            - "threshold": Traditional threshold-based decoding (default)
            - "ml": ML-based decoder using neural network (requires torch)

    Returns:
        List of 3 decoded strings (R, G, B). Empty string for failed layers.

    Raises:
        ValueError: If image is not RGB mode or invalid threshold_method
        ImportError: If method="ml" but torch is not installed
    """
    if img.mode != "RGB":
        raise ValueError("Expected an RGB image")

    # Use ML-based decoder if requested
    if method == "ml":
        from .ml_decoder import decode_rgb_ml, is_torch_available
        if not is_torch_available():
            raise ImportError(
                "PyTorch is required for ML decoder. "
                "Install with: pip install multispecqr[ml]"
            )
        return decode_rgb_ml(img)

    # Validate threshold method
    valid_methods = {"global", "otsu", "adaptive_gaussian", "adaptive_mean"}
    if threshold_method not in valid_methods:
        raise ValueError(
            f"Invalid threshold_method: {threshold_method}. "
            f"Must be one of: {', '.join(valid_methods)}"
        )

    # Apply calibration if provided
    if calibration is not None:
        from .calibration import apply_calibration
        img = apply_calibration(img, calibration)

    arr = np.array(img)  # H x W x 3

    # Apply preprocessing if specified
    if preprocess and preprocess != "none":
        arr = _apply_preprocessing(arr, preprocess)

    results: List[str] = []

    for c in range(3):  # R, G, B
        channel = arr[:, :, c]
        binary = _apply_threshold(channel, threshold_method)
        decoded = _decode_single_layer(binary)
        results.append(decoded or "")

    return results


def decode_layers(
    img: Image.Image,
    num_layers: int | None = None,
    *,
    preprocess: PreprocessMethod | None = None,
    calibration: dict[str, Any] | None = None,
    method: DecodeMethod = "threshold",
) -> List[str]:
    """
    Decode a multi-layer QR image encoded with a color palette.

    Automatically selects the appropriate palette based on num_layers:
    - 1-6 layers: 64-color palette (6-bit)
    - 7-8 layers: 256-color palette (8-bit)
    - 9 layers: 512-color palette (9-bit)

    Args:
        img: RGB PIL Image encoded with encode_layers()
        num_layers: Number of layers to decode (1-9). If None, defaults to 6.
        preprocess: Optional preprocessing:
            - None or "none": No preprocessing
            - "blur": Gaussian blur to reduce noise
            - "denoise": Non-local means denoising
        calibration: Optional calibration data from compute_calibration()
        method: Decoding method to use:
            - "threshold": Traditional threshold-based decoding (default)
            - "ml": ML-based decoder using neural network (requires torch)

    Returns:
        List of decoded strings, one per layer. Empty string for failed layers.

    Raises:
        ValueError: If image is not RGB mode or num_layers > 9
        ImportError: If method="ml" but torch is not installed
    """
    from .palette import _select_palette

    if img.mode != "RGB":
        raise ValueError("Expected an RGB image")

    # Default to 6 layers if not specified
    if num_layers is None:
        num_layers = 6

    if num_layers > 9:
        raise ValueError("Maximum of 9 layers supported")

    # Use ML-based decoder if requested
    if method == "ml":
        from .ml_decoder import decode_layers_ml, is_torch_available
        if not is_torch_available():
            raise ImportError(
                "PyTorch is required for ML decoder. "
                "Install with: pip install multispecqr[ml]"
            )
        return decode_layers_ml(img, num_layers=num_layers)

    # Apply calibration if provided
    if calibration is not None:
        from .calibration import apply_calibration
        img = apply_calibration(img, calibration)

    arr = np.array(img)  # H x W x 3

    # Apply preprocessing if specified
    if preprocess and preprocess != "none":
        arr = _apply_preprocessing(arr, preprocess)

    h, w = arr.shape[:2]

    # Select appropriate palette based on number of layers
    _, inv_palette, num_bits = _select_palette(num_layers)
    palette_colors = np.array(list(inv_palette.keys()), dtype=np.uint8)
    palette_bitvecs = list(inv_palette.values())

    # Reshape image for efficient color matching
    pixels = arr.reshape(-1, 3)  # (H*W, 3)

    # Find nearest palette color for each pixel using Euclidean distance
    distances = np.linalg.norm(
        pixels[:, np.newaxis, :].astype(np.float32) - palette_colors[np.newaxis, :, :].astype(np.float32),
        axis=2
    )
    nearest_idx = np.argmin(distances, axis=1)  # (H*W,)

    # Map each pixel to its bit-vector
    bitvec_array = np.array([palette_bitvecs[i] for i in nearest_idx])  # (H*W, num_bits)
    bitvec_array = bitvec_array.reshape(h, w, num_bits)  # (H, W, num_bits)

    # Extract and decode each layer
    results: List[str] = []
    for layer_idx in range(num_layers):
        # Extract layer: 1 = black module, 0 = white module
        layer = bitvec_array[:, :, layer_idx]

        # Convert to QR-decodable format: 0 = black, 255 = white
        # Then invert for OpenCV detector which expects black modules to be 0
        binary = ((1 - layer) * 255).astype(np.uint8)

        decoded = _decode_single_layer(binary)
        results.append(decoded or "")

    return results
