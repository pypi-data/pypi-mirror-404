"""
Multispectral QR encoder.

Provides:
    encode_rgb(data_r, data_g, data_b, version=4, ec="M") -> PIL.Image
    encode_layers(data_list, version=4, ec="M") -> PIL.Image
"""
from __future__ import annotations

import numpy as np
from PIL import Image
import qrcode

from .palette import _select_palette


def _make_layer(data: str, version: int, ec: str) -> np.ndarray:
    """Return a binary (0/1) numpy array for one QR layer."""
    qr = qrcode.QRCode(
        version=version,
        error_correction=getattr(qrcode.constants, f"ERROR_CORRECT_{ec}"),
    )
    qr.add_data(data)
    qr.make(fit=False)
    img = qr.make_image(fill_color="black", back_color="white").convert("1")
    return (np.array(img) == 0).astype(np.uint8)  # 1 = black module


def encode_rgb(
    data_r: str,
    data_g: str,
    data_b: str,
    *,
    version: int = 4,
    ec: str = "M",
) -> Image.Image:
    """
    Combine three payloads into a single RGB QR image.

    Each payload is encoded as an independent monochrome QR layer,
    then assigned to one color channel: R, G, B.

    Args:
        data_r: Payload string for Red channel
        data_g: Payload string for Green channel
        data_b: Payload string for Blue channel
        version: QR code version 1-40. Higher versions hold more data. Default: 4
        ec: Error correction level - "L", "M", "Q", or "H". Default: "M"

    Returns:
        PIL.Image in RGB mode
    """
    r = _make_layer(data_r, version, ec)
    g = _make_layer(data_g, version, ec)
    b = _make_layer(data_b, version, ec)

    if not (r.shape == g.shape == b.shape):
        raise ValueError("Layers ended up different sizes; pick same version.")

    rgb_stack = np.stack([r * 255, g * 255, b * 255], axis=-1).astype(np.uint8)
    return Image.fromarray(rgb_stack)


def _build_color_lut(codebook: dict, num_bits: int) -> np.ndarray:
    """
    Build a color lookup table from a codebook.
    
    Args:
        codebook: Dict mapping bit-tuples to RGB colors
        num_bits: Number of bits in the bit-vector
        
    Returns:
        Array of shape (2**num_bits, 3) mapping index to RGB color
    """
    num_entries = 2 ** num_bits
    lut = np.full((num_entries, 3), 255, dtype=np.uint8)  # default white
    
    for bits, color in codebook.items():
        # Convert bit-tuple to index: bits[0] + bits[1]*2 + bits[2]*4 + ...
        index = sum(b << i for i, b in enumerate(bits))
        lut[index] = color
    
    return lut


def encode_layers(data_list: list[str], *, version: int = 4, ec: str = "M") -> Image.Image:
    """
    Encode N binary QR layers into a color QR using an appropriate color palette.

    Automatically selects palette based on number of layers:
    - 1-6 layers: 64-color palette (6-bit)
    - 7-8 layers: 256-color palette (8-bit)
    - 9 layers: 512-color palette (9-bit)

    Args:
        data_list: List of payload strings (1-9 layers)
        version: QR code version 1-40. Default: 4
        ec: Error correction level ("L", "M", "Q", "H"). Default: "M"

    Returns:
        PIL.Image in RGB mode

    Raises:
        ValueError: If more than 9 layers provided or empty list
    """
    num_layers = len(data_list)
    if num_layers == 0:
        raise ValueError("At least one layer required.")
    if num_layers > 9:
        raise ValueError("Maximum of 9 layers supported.")

    # Select appropriate palette based on layer count
    codebook, _, num_bits = _select_palette(num_layers)

    # Generate QR layers
    layers = [_make_layer(data, version, ec) for data in data_list]
    shape = layers[0].shape
    if not all(layer.shape == shape for layer in layers):
        raise ValueError("QR layers must all have the same shape.")

    h, w = shape

    # Stack layers into (H, W, num_layers) array
    layer_stack = np.stack(layers, axis=-1)  # (H, W, num_layers)
    
    # Pad with zeros if num_layers < num_bits
    if num_layers < num_bits:
        padding = np.zeros((h, w, num_bits - num_layers), dtype=np.uint8)
        layer_stack = np.concatenate([layer_stack, padding], axis=-1)  # (H, W, num_bits)

    # Convert bit-vectors to indices: index = sum(bit[i] * 2^i)
    # Create powers of 2: [1, 2, 4, 8, ...]
    powers = (1 << np.arange(num_bits, dtype=np.uint32))  # [1, 2, 4, 8, 16, ...]
    
    # Compute index for each pixel: (H, W, num_bits) @ (num_bits,) -> (H, W)
    indices = layer_stack.astype(np.uint32) @ powers  # (H, W)

    # Build lookup table and apply
    lut = _build_color_lut(codebook, num_bits)  # (2^num_bits, 3)
    img_arr = lut[indices]  # (H, W, 3)

    return Image.fromarray(img_arr)
