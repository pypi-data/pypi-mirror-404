"""
Command-line interface for multispecqr.

Usage examples:
    # RGB mode: encode three payloads
    python -m multispecqr encode "RED" "GREEN" "BLUE" out.png

    # RGB mode: encode with options
    python -m multispecqr encode "RED" "GREEN" "BLUE" out.png --version 4 --ec H

    # Palette mode: encode up to 9 payloads
    python -m multispecqr encode "L1" "L2" "L3" "L4" "L5" "L6" out.png --mode palette

    # Decode with robustness options
    python -m multispecqr decode image.png --threshold otsu --preprocess blur

    # Decode to JSON
    python -m multispecqr decode image.png --json

    # Generate calibration card
    python -m multispecqr calibrate calibration.png

    # Batch decode multiple images
    python -m multispecqr batch-decode img1.png img2.png --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from PIL import Image

from .encoder import encode_rgb, encode_layers
from .decoder import decode_rgb, decode_layers
from .calibration import generate_calibration_card


def _cmd_encode(args: argparse.Namespace) -> None:
    """Handle the encode command."""
    payloads = args.data

    if args.mode == "rgb":
        if len(payloads) != 3:
            print(f"Error: RGB mode requires exactly 3 payloads, got {len(payloads)}", file=sys.stderr)
            sys.exit(1)
        img = encode_rgb(payloads[0], payloads[1], payloads[2], version=args.version, ec=args.ec)
        mode_str = "RGB"
    else:  # palette mode
        if len(payloads) < 1 or len(payloads) > 9:
            print(f"Error: Palette mode requires 1-9 payloads, got {len(payloads)}", file=sys.stderr)
            sys.exit(1)
        img = encode_layers(payloads, version=args.version, ec=args.ec)
        mode_str = f"palette ({len(payloads)} layers)"

    # Apply scale if specified
    if args.scale and args.scale > 1:
        new_size = (img.width * args.scale, img.height * args.scale)
        img = img.resize(new_size, Image.NEAREST)

    img.save(args.output)
    print(f"Saved {mode_str} QR to {args.output}")


def _cmd_decode(args: argparse.Namespace) -> None:
    """Handle the decode command."""
    try:
        img = Image.open(args.image_path)
    except FileNotFoundError:
        print(f"Error: File not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    if img.mode != "RGB":
        print(f"Error: Expected RGB image, got {img.mode}", file=sys.stderr)
        sys.exit(1)

    if args.mode == "rgb":
        # RGB mode supports threshold_method and preprocess
        decode_kwargs = {}
        if args.threshold:
            decode_kwargs["threshold_method"] = args.threshold
        if args.preprocess:
            decode_kwargs["preprocess"] = args.preprocess
        payloads = decode_rgb(img, **decode_kwargs)
        labels = ["R", "G", "B"]
    else:  # palette mode
        # Palette mode only supports preprocess (uses color matching, not thresholding)
        decode_kwargs = {}
        if args.preprocess:
            decode_kwargs["preprocess"] = args.preprocess
        payloads = decode_layers(img, num_layers=args.layers, **decode_kwargs)
        labels = [f"L{i+1}" for i in range(len(payloads))]

    # Output results
    if args.json:
        data = {label: text for label, text in zip(labels, payloads)}
        print(json.dumps(data, indent=2))
    else:
        print("Decoded layers:")
        for label, text in zip(labels, payloads):
            if text:
                print(f"  {label}: {text!r}")
            else:
                print(f"  {label}: (empty or failed to decode)")


def _cmd_calibrate(args: argparse.Namespace) -> None:
    """Handle the calibrate command."""
    card = generate_calibration_card(
        patch_size=args.patch_size,
        padding=args.padding
    )
    card.save(args.output)
    print(f"Saved calibration card to {args.output}")


def _cmd_batch_decode(args: argparse.Namespace) -> None:
    """Handle the batch-decode command."""
    results: List[dict] = []

    for image_path in args.images:
        path = Path(image_path)
        entry = {"file": str(path)}

        try:
            img = Image.open(path)
            if img.mode != "RGB":
                entry["error"] = f"Expected RGB image, got {img.mode}"
            else:
                if args.mode == "rgb":
                    # RGB mode supports threshold_method and preprocess
                    decode_kwargs = {}
                    if args.threshold:
                        decode_kwargs["threshold_method"] = args.threshold
                    if args.preprocess:
                        decode_kwargs["preprocess"] = args.preprocess
                    payloads = decode_rgb(img, **decode_kwargs)
                    labels = ["R", "G", "B"]
                else:
                    # Palette mode only supports preprocess
                    decode_kwargs = {}
                    if args.preprocess:
                        decode_kwargs["preprocess"] = args.preprocess
                    payloads = decode_layers(img, num_layers=args.layers, **decode_kwargs)
                    labels = [f"L{i+1}" for i in range(len(payloads))]

                entry["data"] = {label: text for label, text in zip(labels, payloads)}

        except FileNotFoundError:
            entry["error"] = "File not found"
        except Exception as e:
            entry["error"] = str(e)

        results.append(entry)

    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for entry in results:
            print(f"\n{entry['file']}:")
            if "error" in entry:
                print(f"  Error: {entry['error']}")
            else:
                for label, text in entry["data"].items():
                    if text:
                        print(f"  {label}: {text!r}")
                    else:
                        print(f"  {label}: (empty or failed)")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="multispecqr",
        description="Encode and decode multi-spectral QR codes",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Encode command
    enc = sub.add_parser(
        "encode",
        help="Encode payloads into a multi-spectral QR image",
        description="Encode 1-9 payloads into a single QR code image using color channels.",
    )
    enc.add_argument(
        "data",
        nargs="+",
        help="Payload strings to encode (3 for RGB mode, 1-9 for palette mode)",
    )
    enc.add_argument(
        "output",
        type=Path,
        help="Output image path (e.g., output.png)",
    )
    enc.add_argument(
        "--mode", "-m",
        choices=["rgb", "palette"],
        default="rgb",
        help="Encoding mode: 'rgb' (3 layers) or 'palette' (1-9 layers). Default: rgb",
    )
    enc.add_argument(
        "--version", "-v",
        type=int,
        default=4,
        help="QR code version (1-40). Higher = more capacity. Default: 4",
    )
    enc.add_argument(
        "--ec", "-e",
        choices=["L", "M", "Q", "H"],
        default="M",
        help="Error correction level. L=7%%, M=15%%, Q=25%%, H=30%%. Default: M",
    )
    enc.add_argument(
        "--scale", "-s",
        type=int,
        default=1,
        help="Scale factor for output image. Default: 1 (no scaling)",
    )
    enc.set_defaults(func=_cmd_encode)

    # Decode command
    dec = sub.add_parser(
        "decode",
        help="Decode a multi-spectral QR image",
        description="Decode a multi-spectral QR code image back to its payloads.",
    )
    dec.add_argument(
        "image_path",
        type=Path,
        help="Path to the QR image to decode",
    )
    dec.add_argument(
        "--mode", "-m",
        choices=["rgb", "palette"],
        default="rgb",
        help="Decoding mode: 'rgb' (3 layers) or 'palette' (1-9 layers). Default: rgb",
    )
    dec.add_argument(
        "--layers", "-l",
        type=int,
        default=6,
        help="Number of layers to decode in palette mode (1-9). Default: 6",
    )
    dec.add_argument(
        "--threshold", "-t",
        choices=["global", "otsu", "adaptive_gaussian", "adaptive_mean"],
        default=None,
        help="Thresholding method for robustness. Default: global",
    )
    dec.add_argument(
        "--preprocess", "-p",
        choices=["none", "blur", "denoise"],
        default=None,
        help="Preprocessing method for noise reduction. Default: none",
    )
    dec.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results as JSON",
    )
    dec.set_defaults(func=_cmd_decode)

    # Calibrate command
    cal = sub.add_parser(
        "calibrate",
        help="Generate a color calibration card",
        description="Generate a calibration card with all palette colors for camera color correction.",
    )
    cal.add_argument(
        "output",
        type=Path,
        help="Output image path for calibration card",
    )
    cal.add_argument(
        "--patch-size",
        type=int,
        default=50,
        help="Size of each color patch in pixels. Default: 50",
    )
    cal.add_argument(
        "--padding",
        type=int,
        default=5,
        help="Padding between patches. Default: 5",
    )
    cal.set_defaults(func=_cmd_calibrate)

    # Batch decode command
    batch = sub.add_parser(
        "batch-decode",
        help="Decode multiple QR images at once",
        description="Decode multiple multi-spectral QR code images in batch.",
    )
    batch.add_argument(
        "images",
        nargs="+",
        help="Paths to QR images to decode",
    )
    batch.add_argument(
        "--mode", "-m",
        choices=["rgb", "palette"],
        default="rgb",
        help="Decoding mode: 'rgb' or 'palette'. Default: rgb",
    )
    batch.add_argument(
        "--layers", "-l",
        type=int,
        default=6,
        help="Number of layers (palette mode). Default: 6",
    )
    batch.add_argument(
        "--threshold", "-t",
        choices=["global", "otsu", "adaptive_gaussian", "adaptive_mean"],
        default=None,
        help="Thresholding method. Default: global",
    )
    batch.add_argument(
        "--preprocess", "-p",
        choices=["none", "blur", "denoise"],
        default=None,
        help="Preprocessing method. Default: none",
    )
    batch.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results as JSON",
    )
    batch.set_defaults(func=_cmd_batch_decode)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
