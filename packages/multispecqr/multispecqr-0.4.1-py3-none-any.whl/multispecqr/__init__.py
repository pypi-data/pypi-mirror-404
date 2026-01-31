"""multispecqr - Multi-spectral QR codes with multiple data layers."""

from .__about__ import __version__

# Public API
from .encoder import encode_rgb, encode_layers
from .decoder import decode_rgb, decode_layers
from .palette import palette_6, inverse_palette_6, palette_8, inverse_palette_8, palette_9, inverse_palette_9
from .calibration import generate_calibration_card, compute_calibration, apply_calibration

# ML decoder is optional - import fails gracefully if torch not installed
try:
    from . import ml_decoder
    _ml_available = True
except ImportError:
    ml_decoder = None  # type: ignore
    _ml_available = False

__all__ = [
    "__version__",
    "encode_rgb",
    "encode_layers",
    "decode_rgb",
    "decode_layers",
    "palette_6",
    "inverse_palette_6",
    "palette_8",
    "inverse_palette_8",
    "palette_9",
    "inverse_palette_9",
    "generate_calibration_card",
    "compute_calibration",
    "apply_calibration",
    "ml_decoder",
]
