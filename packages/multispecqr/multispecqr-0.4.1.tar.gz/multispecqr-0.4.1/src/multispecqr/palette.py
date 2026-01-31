"""
Color palettes & codebooks for extended-layer QR.

Provides palettes supporting various layer counts:
- 6-layer: 64 colors (2 bits per channel)
- 8-layer: 256 colors (3-3-2 bit distribution)
- 9-layer: 512 colors (3 bits per channel)

Color encoding schemes:
- 6-layer: bits 0-1 → R, bits 2-3 → G, bits 4-5 → B (4 levels each)
- 8-layer: bits 0-2 → R, bits 3-5 → G, bits 6-7 → B (8-8-4 levels)
- 9-layer: bits 0-2 → R, bits 3-5 → G, bits 6-8 → B (8 levels each)
"""
from __future__ import annotations

from typing import Dict, Tuple
import itertools


# =============================================================================
# 6-Layer Palette (64 colors) - Original implementation
# =============================================================================

def _bitvec_to_color_6(bits: Tuple[int, ...]) -> Tuple[int, int, int]:
    """Convert a 6-bit vector to an RGB color."""
    # Ensure we have exactly 6 bits
    bits = tuple(bits) + (0,) * (6 - len(bits))

    # Combine pairs of bits into 2-bit values (0-3), then scale to 0-255
    r_level = bits[0] + bits[1] * 2  # 0-3
    g_level = bits[2] + bits[3] * 2  # 0-3
    b_level = bits[4] + bits[5] * 2  # 0-3

    return (r_level * 85, g_level * 85, b_level * 85)


def _color_to_bitvec_6(r: int, g: int, b: int) -> Tuple[int, ...]:
    """Convert an RGB color to a 6-bit vector."""
    # Quantize to nearest level (0, 85, 170, 255)
    r_level = min(3, max(0, round(r / 85)))
    g_level = min(3, max(0, round(g / 85)))
    b_level = min(3, max(0, round(b / 85)))

    # Extract individual bits
    return (
        r_level % 2, r_level // 2,
        g_level % 2, g_level // 2,
        b_level % 2, b_level // 2,
    )


def _build_palette_64() -> Dict[Tuple[int, ...], Tuple[int, int, int]]:
    """Generate all 64 bit-vector to color mappings."""
    palette = {}
    for bits in itertools.product([0, 1], repeat=6):
        palette[bits] = _bitvec_to_color_6(bits)
    return palette


_PALETTE_64 = _build_palette_64()


def palette_6() -> Dict[Tuple[int, ...], Tuple[int, int, int]]:
    """Return the 6-layer bit-vector -> RGB codebook (64 colors)."""
    return _PALETTE_64.copy()


def inverse_palette_6() -> Dict[Tuple[int, int, int], Tuple[int, ...]]:
    """Return the inverse codebook: RGB triplet -> bit-vector."""
    return {color: bitvec for bitvec, color in _PALETTE_64.items()}


# =============================================================================
# 8-Layer Palette (256 colors) - 3-3-2 bit distribution
# =============================================================================

def _bitvec_to_color_8(bits: Tuple[int, ...]) -> Tuple[int, int, int]:
    """
    Convert an 8-bit vector to an RGB color using 3-3-2 distribution.

    - bits 0-2: R channel (8 levels)
    - bits 3-5: G channel (8 levels)
    - bits 6-7: B channel (4 levels)
    """
    bits = tuple(bits) + (0,) * (8 - len(bits))

    # R: 3 bits → 8 levels
    r_level = bits[0] + bits[1] * 2 + bits[2] * 4  # 0-7
    # G: 3 bits → 8 levels
    g_level = bits[3] + bits[4] * 2 + bits[5] * 4  # 0-7
    # B: 2 bits → 4 levels
    b_level = bits[6] + bits[7] * 2  # 0-3

    # Scale to 0-255
    r = round(r_level * 255 / 7)
    g = round(g_level * 255 / 7)
    b = round(b_level * 255 / 3)

    return (r, g, b)


def _color_to_bitvec_8(r: int, g: int, b: int) -> Tuple[int, ...]:
    """Convert an RGB color to an 8-bit vector using 3-3-2 distribution."""
    # Quantize to nearest levels
    r_level = min(7, max(0, round(r * 7 / 255)))
    g_level = min(7, max(0, round(g * 7 / 255)))
    b_level = min(3, max(0, round(b * 3 / 255)))

    return (
        r_level % 2, (r_level // 2) % 2, r_level // 4,
        g_level % 2, (g_level // 2) % 2, g_level // 4,
        b_level % 2, b_level // 2,
    )


def _build_palette_256() -> Dict[Tuple[int, ...], Tuple[int, int, int]]:
    """Generate all 256 bit-vector to color mappings."""
    palette = {}
    for bits in itertools.product([0, 1], repeat=8):
        palette[bits] = _bitvec_to_color_8(bits)
    return palette


_PALETTE_256 = _build_palette_256()


def palette_8() -> Dict[Tuple[int, ...], Tuple[int, int, int]]:
    """Return the 8-layer bit-vector -> RGB codebook (256 colors)."""
    return _PALETTE_256.copy()


def inverse_palette_8() -> Dict[Tuple[int, int, int], Tuple[int, ...]]:
    """Return the inverse codebook: RGB triplet -> bit-vector."""
    return {color: bitvec for bitvec, color in _PALETTE_256.items()}


# =============================================================================
# 9-Layer Palette (512 colors) - 3-3-3 bit distribution
# =============================================================================

def _bitvec_to_color_9(bits: Tuple[int, ...]) -> Tuple[int, int, int]:
    """
    Convert a 9-bit vector to an RGB color using 3-3-3 distribution.

    - bits 0-2: R channel (8 levels)
    - bits 3-5: G channel (8 levels)
    - bits 6-8: B channel (8 levels)
    """
    bits = tuple(bits) + (0,) * (9 - len(bits))

    # Each channel: 3 bits → 8 levels
    r_level = bits[0] + bits[1] * 2 + bits[2] * 4  # 0-7
    g_level = bits[3] + bits[4] * 2 + bits[5] * 4  # 0-7
    b_level = bits[6] + bits[7] * 2 + bits[8] * 4  # 0-7

    # Scale to 0-255
    r = round(r_level * 255 / 7)
    g = round(g_level * 255 / 7)
    b = round(b_level * 255 / 7)

    return (r, g, b)


def _color_to_bitvec_9(r: int, g: int, b: int) -> Tuple[int, ...]:
    """Convert an RGB color to a 9-bit vector using 3-3-3 distribution."""
    # Quantize to nearest levels (8 levels per channel)
    r_level = min(7, max(0, round(r * 7 / 255)))
    g_level = min(7, max(0, round(g * 7 / 255)))
    b_level = min(7, max(0, round(b * 7 / 255)))

    return (
        r_level % 2, (r_level // 2) % 2, r_level // 4,
        g_level % 2, (g_level // 2) % 2, g_level // 4,
        b_level % 2, (b_level // 2) % 2, b_level // 4,
    )


def _build_palette_512() -> Dict[Tuple[int, ...], Tuple[int, int, int]]:
    """Generate all 512 bit-vector to color mappings."""
    palette = {}
    for bits in itertools.product([0, 1], repeat=9):
        palette[bits] = _bitvec_to_color_9(bits)
    return palette


_PALETTE_512 = _build_palette_512()


def palette_9() -> Dict[Tuple[int, ...], Tuple[int, int, int]]:
    """Return the 9-layer bit-vector -> RGB codebook (512 colors)."""
    return _PALETTE_512.copy()


def inverse_palette_9() -> Dict[Tuple[int, int, int], Tuple[int, ...]]:
    """Return the inverse codebook: RGB triplet -> bit-vector."""
    return {color: bitvec for bitvec, color in _PALETTE_512.items()}


# =============================================================================
# Palette Selection Helper
# =============================================================================

def _select_palette(num_layers: int):
    """
    Select the appropriate palette based on number of layers.

    Returns:
        (palette, inverse_palette, num_bits) tuple
    """
    if num_layers <= 6:
        return palette_6(), inverse_palette_6(), 6
    elif num_layers <= 8:
        return palette_8(), inverse_palette_8(), 8
    elif num_layers <= 9:
        return palette_9(), inverse_palette_9(), 9
    else:
        raise ValueError(f"Maximum of 9 layers supported, got {num_layers}")


# Legacy aliases for backwards compatibility
_bitvec_to_color = _bitvec_to_color_6
_color_to_bitvec = _color_to_bitvec_6
