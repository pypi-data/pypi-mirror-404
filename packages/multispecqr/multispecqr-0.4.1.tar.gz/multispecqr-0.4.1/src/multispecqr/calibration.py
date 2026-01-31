"""
Color calibration helpers for robust QR decoding.

Provides functions to generate calibration cards, compute color correction
from reference images, and apply calibration to improve decoding accuracy.

Functions:
    generate_calibration_card() -> PIL.Image
    compute_calibration(reference, sample) -> dict
    apply_calibration(img, calibration) -> PIL.Image
"""
from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image

from .palette import palette_6


def generate_calibration_card(
    patch_size: int = 50,
    padding: int = 5,
) -> Image.Image:
    """
    Generate a calibration card containing all 64 palette colors.

    The card can be used as a reference for color calibration. Print the card,
    photograph it, then use compute_calibration() to compute a color correction.

    Args:
        patch_size: Size of each color patch in pixels
        padding: Padding between patches in pixels

    Returns:
        PIL Image containing the calibration card
    """
    palette = palette_6()
    colors = list(palette.values())
    n_colors = len(colors)

    # Arrange colors in an 8x8 grid
    cols = 8
    rows = (n_colors + cols - 1) // cols

    # Calculate image dimensions
    width = cols * (patch_size + padding) + padding
    height = rows * (patch_size + padding) + padding

    # Create white background
    img_arr = np.ones((height, width, 3), dtype=np.uint8) * 255

    # Draw color patches
    for i, color in enumerate(colors):
        row = i // cols
        col = i % cols

        y = padding + row * (patch_size + padding)
        x = padding + col * (patch_size + padding)

        img_arr[y:y + patch_size, x:x + patch_size] = color

    return Image.fromarray(img_arr)


def _extract_patch_colors(
    img: Image.Image,
    patch_size: int = 50,
    padding: int = 5,
) -> np.ndarray:
    """
    Extract the average color from each patch in a calibration card image.

    Args:
        img: Calibration card image
        patch_size: Expected size of each color patch
        padding: Expected padding between patches

    Returns:
        Array of shape (64, 3) with RGB values for each patch
    """
    arr = np.array(img)
    colors = []

    cols = 8
    rows = 8

    for i in range(rows * cols):
        row = i // cols
        col = i % cols

        y = padding + row * (patch_size + padding)
        x = padding + col * (patch_size + padding)

        # Extract center region of patch to avoid edge effects
        margin = patch_size // 4
        patch = arr[y + margin:y + patch_size - margin, x + margin:x + patch_size - margin]

        # Compute mean color
        mean_color = patch.mean(axis=(0, 1))
        colors.append(mean_color)

    return np.array(colors, dtype=np.float32)


def compute_calibration(
    reference: Image.Image,
    sample: Image.Image,
    *,
    patch_size: int = 50,
    padding: int = 5,
) -> dict[str, Any]:
    """
    Compute color calibration from a reference and sample calibration card.

    The reference should be the original generate_calibration_card() output.
    The sample should be a photograph of the printed calibration card.

    Args:
        reference: Original calibration card image
        sample: Photographed calibration card image
        patch_size: Size of color patches
        padding: Padding between patches

    Returns:
        Calibration data dict containing:
            - "matrix": 3x3 color correction matrix
            - "offset": RGB offset vector
            - "method": Calibration method used
    """
    # Extract colors from both images
    ref_colors = _extract_patch_colors(reference, patch_size, padding)
    sample_colors = _extract_patch_colors(sample, patch_size, padding)

    # Compute affine color transformation using least squares
    # sample_colors @ matrix + offset ≈ ref_colors

    # Add bias term for offset
    n = len(sample_colors)
    sample_augmented = np.hstack([sample_colors, np.ones((n, 1))])

    # Solve for each output channel
    matrix = np.zeros((3, 4), dtype=np.float32)
    for c in range(3):
        # Solve: sample_augmented @ params = ref_colors[:, c]
        params, _, _, _ = np.linalg.lstsq(sample_augmented, ref_colors[:, c], rcond=None)
        matrix[c] = params

    # Extract 3x3 matrix and offset
    color_matrix = matrix[:, :3]
    offset = matrix[:, 3]

    return {
        "matrix": color_matrix,
        "offset": offset,
        "method": "affine",
    }


def apply_calibration(
    img: Image.Image,
    calibration: dict[str, Any],
) -> Image.Image:
    """
    Apply color calibration to an image.

    Args:
        img: Input image to calibrate
        calibration: Calibration data from compute_calibration()

    Returns:
        Color-corrected PIL Image
    """
    if calibration is None:
        return img

    arr = np.array(img).astype(np.float32)
    original_shape = arr.shape

    # Reshape to (N, 3)
    pixels = arr.reshape(-1, 3)

    method = calibration.get("method", "affine")

    if method == "affine":
        matrix = calibration["matrix"]
        offset = calibration["offset"]

        # Apply affine transformation: output = pixels @ matrix.T + offset
        corrected = pixels @ matrix.T + offset

    elif method == "lut":
        # Lookup table method (future expansion)
        lut = calibration["lut"]
        corrected = lut[pixels[:, 0].astype(int), pixels[:, 1].astype(int), pixels[:, 2].astype(int)]

    else:
        # Unknown method, return unchanged
        return img

    # Clip to valid range and reshape
    corrected = np.clip(corrected, 0, 255).astype(np.uint8)
    corrected = corrected.reshape(original_shape)

    return Image.fromarray(corrected)
