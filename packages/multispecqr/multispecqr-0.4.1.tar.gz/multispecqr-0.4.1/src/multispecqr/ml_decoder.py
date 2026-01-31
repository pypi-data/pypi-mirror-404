"""
ML-based decoder for multi-spectral QR codes.

Uses lightweight CNNs to unmix color layers, providing better robustness
for real-world images with noise, compression artifacts, and color distortion.

Provides two separate decoders:
- RGBMLDecoder: For RGB-encoded images (3 layers)
- PaletteMLDecoder: For palette-encoded images (6-9 layers)

Requires optional 'ml' dependencies: pip install multispecqr[ml]
"""
from __future__ import annotations

from typing import List, Tuple, Any
import numpy as np
from PIL import Image

# Check if torch is available
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None


def is_torch_available() -> bool:
    """Check if PyTorch is available."""
    return TORCH_AVAILABLE


def _num_layers_to_model_bits(num_layers: int) -> int:
    """
    Map user-requested layers to the model output size.
    
    This matches the palette selection logic:
    - 1-6 layers → 6-bit model (64-color palette)
    - 7-8 layers → 8-bit model (256-color palette)
    - 9 layers → 9-bit model (512-color palette)
    
    Args:
        num_layers: Number of data layers (1-9)
        
    Returns:
        Number of model output channels (6, 8, or 9)
    """
    if num_layers < 1 or num_layers > 9:
        raise ValueError(f"num_layers must be 1-9, got {num_layers}")
    
    if num_layers <= 6:
        return 6
    elif num_layers <= 8:
        return 8
    else:
        return 9


def _detect_nvidia_gpu() -> bool:
    """
    Detect if an NVIDIA GPU is present on the system.
    
    Uses nvidia-smi to check for GPU presence, independent of PyTorch.
    """
    import subprocess
    import shutil
    
    if shutil.which("nvidia-smi") is None:
        return False
    
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and len(result.stdout.strip()) > 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _check_gpu_advisory() -> None:
    """Check if user has a GPU but PyTorch can't use it."""
    if not TORCH_AVAILABLE:
        return
    
    if torch.cuda.is_available():
        return
    
    if not _detect_nvidia_gpu():
        return
    
    import warnings
    msg = (
        "NVIDIA GPU detected but PyTorch is using CPU. "
        "For faster ML decoding, install CUDA-enabled PyTorch: "
        "pip uninstall torch torchvision -y && "
        "pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124"
    )
    warnings.warn(msg, stacklevel=3)


_GPU_ADVISORY_SHOWN = False


def _maybe_show_gpu_advisory() -> None:
    """Show GPU advisory once per session."""
    global _GPU_ADVISORY_SHOWN
    if not _GPU_ADVISORY_SHOWN:
        _check_gpu_advisory()
        _GPU_ADVISORY_SHOWN = True


if TORCH_AVAILABLE:
    class LayerUnmixingCNN(nn.Module):
        """
        CNN for unmixing multi-spectral QR code colors.
        
        Configurable output channels for RGB (3) or palette (6/8/9) modes.
        """

        def __init__(self, num_outputs: int = 6):
            super().__init__()
            
            self.num_outputs = num_outputs

            # Encoder
            self.enc1 = nn.Sequential(
                nn.Conv2d(3, 32, kernel_size=3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.Conv2d(32, 32, kernel_size=3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
            )

            self.enc2 = nn.Sequential(
                nn.Conv2d(32, 64, kernel_size=3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.Conv2d(64, 64, kernel_size=3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
            )

            # Decoder
            self.dec1 = nn.Sequential(
                nn.Conv2d(64, 32, kernel_size=3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.Conv2d(32, 32, kernel_size=3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
            )

            # Output layer
            self.output = nn.Conv2d(32, num_outputs, kernel_size=1)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            e1 = self.enc1(x)
            e2 = self.enc2(e1)
            d1 = self.dec1(e2)
            out = self.output(d1)
            return torch.sigmoid(out)


class _BaseMLDecoder:
    """Base class for ML decoders."""
    
    # HuggingFace model repository base
    HF_REPO_BASE = "Jemsbhai/multispecqr"
    
    def __init__(self, num_outputs: int, device: str | None = None):
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch is required for ML decoder. "
                "Install with: pip install multispecqr[ml]"
            )

        _maybe_show_gpu_advisory()

        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = torch.device(device)
        self.num_outputs = num_outputs

        self.model = LayerUnmixingCNN(num_outputs=num_outputs).to(self.device)
        self.model.eval()

        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.BCELoss()

    def preprocess(self, img: Image.Image) -> torch.Tensor:
        """Preprocess an image for the model."""
        arr = np.array(img).astype(np.float32) / 255.0
        arr = arr.transpose(2, 0, 1)
        tensor = torch.from_numpy(arr).unsqueeze(0).to(self.device)
        return tensor

    def postprocess(self, output: torch.Tensor) -> np.ndarray:
        """Postprocess model output to binary layers."""
        arr = output.squeeze(0).detach().cpu().numpy()
        arr = arr.transpose(1, 2, 0)
        binary = (arr > 0.5).astype(np.uint8)
        return binary

    def predict_layers(self, img: Image.Image) -> np.ndarray:
        """Predict binary layers from an image."""
        self.model.eval()
        with torch.no_grad():
            x = self.preprocess(img)
            output = self.model(x)
            return self.postprocess(output)

    def save(self, path: str) -> None:
        """
        Save model weights to a file.
        
        Args:
            path: Path to save the model (e.g., 'model.pt')
            
        Example:
            >>> decoder = RGBMLDecoder()
            >>> decoder.train_epoch(num_samples=100)
            >>> decoder.save('rgb_decoder.pt')
        """
        state = {
            'model_state_dict': self.model.state_dict(),
            'num_outputs': self.num_outputs,
            'model_class': self.__class__.__name__,
        }
        # Add num_layers for PaletteMLDecoder
        if hasattr(self, 'num_layers'):
            state['num_layers'] = self.num_layers
            state['model_bits'] = self.model_bits
        
        torch.save(state, path)
    
    def load(self, path: str) -> None:
        """
        Load model weights from a file.
        
        Args:
            path: Path to the saved model
            
        Example:
            >>> decoder = RGBMLDecoder()
            >>> decoder.load('rgb_decoder.pt')
        """
        state = torch.load(path, map_location=self.device, weights_only=False)
        
        # Validate model compatibility
        if state['num_outputs'] != self.num_outputs:
            raise ValueError(
                f"Model mismatch: saved model has {state['num_outputs']} outputs, "
                f"but decoder expects {self.num_outputs}"
            )
        
        self.model.load_state_dict(state['model_state_dict'])
        self.model.eval()
    
    @classmethod
    def from_local(
        cls,
        path: str,
        device: str | None = None,
    ):
        """
        Load a model from a local file with automatic type detection.
        
        This is the recommended way to load locally saved models, as it
        automatically detects whether the model is RGB or Palette and
        creates the appropriate decoder instance.
        
        Args:
            path: Path to the saved model file (e.g., 'model.pt')
            device: Device to load model on ('cuda' or 'cpu'). Auto-detected if None.
            
        Returns:
            Loaded decoder instance (RGBMLDecoder or PaletteMLDecoder).
            
        Example:
            >>> # Load any saved model without knowing its type
            >>> decoder = RGBMLDecoder.from_local('my_model.pt')
            >>> # Or equivalently:
            >>> decoder = PaletteMLDecoder.from_local('my_model.pt')
            
            >>> # Train and save your own model
            >>> decoder = PaletteMLDecoder(num_layers=8)
            >>> decoder.train_epoch(num_samples=500)
            >>> decoder.save('my_palette8.pt')
            >>> 
            >>> # Later, load it back
            >>> decoder = PaletteMLDecoder.from_local('my_palette8.pt')
        """
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch is required for ML decoder. "
                "Install with: pip install multispecqr[ml]"
            )
        
        # Load state to check model type
        state = torch.load(path, map_location='cpu', weights_only=False)
        
        model_class = state.get('model_class', 'PaletteMLDecoder')
        
        # Create appropriate decoder instance
        if model_class == 'RGBMLDecoder':
            decoder = RGBMLDecoder(device=device)
        else:
            num_layers = state.get('num_layers', 6)
            decoder = PaletteMLDecoder(num_layers=num_layers, device=device)
        
        decoder.load(path)
        return decoder
    
    def push_to_hub(
        self,
        repo_id: str | None = None,
        token: str | None = None,
        private: bool = False,
        commit_message: str = "Upload MultiSpecQR model",
    ) -> str:
        """
        Push model to HuggingFace Hub.
        
        Args:
            repo_id: Repository ID (e.g., 'username/model-name'). 
                     If None, uses default based on model type.
            token: HuggingFace API token. Uses cached token if None.
            private: Whether to create a private repository.
            commit_message: Commit message for the upload.
            
        Returns:
            URL of the uploaded model.
            
        Example:
            >>> decoder = RGBMLDecoder()
            >>> decoder.train_epoch(num_samples=1000)
            >>> decoder.push_to_hub('jemsbhai/multispecqr-rgb-v2')
        """
        try:
            from huggingface_hub import HfApi, hf_hub_download
        except ImportError:
            raise ImportError(
                "huggingface_hub is required for push_to_hub. "
                "Install with: pip install huggingface_hub"
            )
        
        import tempfile
        import os
        
        # Default repo name based on model type
        if repo_id is None:
            if isinstance(self, RGBMLDecoder):
                repo_id = f"{self.HF_REPO_BASE}-rgb"
            else:
                repo_id = f"{self.HF_REPO_BASE}-palette{self.num_layers}"
        
        api = HfApi()
        
        # Create repo if it doesn't exist
        api.create_repo(repo_id, exist_ok=True, private=private, token=token)
        
        # Save model to temp file and upload
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "model.pt")
            self.save(model_path)
            
            # Create a simple README
            readme_path = os.path.join(tmpdir, "README.md")
            with open(readme_path, "w") as f:
                f.write(self._generate_model_card())
            
            # Upload files
            api.upload_file(
                path_or_fileobj=model_path,
                path_in_repo="model.pt",
                repo_id=repo_id,
                token=token,
                commit_message=commit_message,
            )
            api.upload_file(
                path_or_fileobj=readme_path,
                path_in_repo="README.md",
                repo_id=repo_id,
                token=token,
                commit_message=commit_message,
            )
        
        url = f"https://huggingface.co/{repo_id}"
        print(f"Model pushed to: {url}")
        return url
    
    def _generate_model_card(self) -> str:
        """Generate a model card README for HuggingFace."""
        if isinstance(self, RGBMLDecoder):
            model_type = "RGB"
            num_layers = 3
        else:
            model_type = "Palette"
            num_layers = getattr(self, 'num_layers', 6)
        
        return f"""---
tags:
- multispecqr
- qr-code
- image-processing
library_name: multispecqr
---

# MultiSpecQR {model_type} Decoder

Pre-trained ML decoder for multi-spectral QR codes.

## Model Details

- **Type**: {model_type}MLDecoder
- **Outputs**: {self.num_outputs} layers
- **Architecture**: LayerUnmixingCNN

## Usage

```python
from multispecqr.ml_decoder import {model_type}MLDecoder

# Load pre-trained model
decoder = {model_type}MLDecoder.from_pretrained("{self.HF_REPO_BASE}-{model_type.lower()}{num_layers if model_type == 'Palette' else ''}")

# Decode an image
results = decoder.decode(image)
```

## Training

This model was trained on synthetically generated QR codes using the MultiSpecQR library.

## Links

- [MultiSpecQR GitHub](https://github.com/jemsbhai/multispecqr)
- [MultiSpecQR PyPI](https://pypi.org/project/multispecqr/)
"""
    
    @classmethod
    def from_pretrained(
        cls,
        repo_id: str,
        token: str | None = None,
        device: str | None = None,
        **kwargs,
    ):
        """
        Load a pre-trained model from HuggingFace Hub.
        
        Args:
            repo_id: Repository ID (e.g., 'jemsbhai/multispecqr-rgb')
            token: HuggingFace API token. Uses cached token if None.
            device: Device to load model on ('cuda' or 'cpu').
            **kwargs: Additional arguments passed to decoder constructor.
            
        Returns:
            Loaded decoder instance.
            
        Example:
            >>> decoder = RGBMLDecoder.from_pretrained('jemsbhai/multispecqr-rgb')
            >>> results = decoder.decode(image)
        """
        try:
            from huggingface_hub import hf_hub_download
        except ImportError:
            raise ImportError(
                "huggingface_hub is required for from_pretrained. "
                "Install with: pip install huggingface_hub"
            )
        
        # Download model file
        model_path = hf_hub_download(
            repo_id=repo_id,
            filename="model.pt",
            token=token,
        )
        
        # Load state to check model type
        state = torch.load(model_path, map_location='cpu', weights_only=False)
        
        # Create appropriate decoder instance
        if cls == _BaseMLDecoder:
            # Called from base class - determine type from state
            if state.get('model_class') == 'RGBMLDecoder':
                decoder = RGBMLDecoder(device=device)
            else:
                num_layers = state.get('num_layers', 6)
                decoder = PaletteMLDecoder(num_layers=num_layers, device=device, **kwargs)
        else:
            # Called from subclass
            if cls == PaletteMLDecoder:
                num_layers = kwargs.pop('num_layers', state.get('num_layers', 6))
                decoder = cls(num_layers=num_layers, device=device, **kwargs)
            else:
                decoder = cls(device=device, **kwargs)
        
        decoder.load(model_path)
        return decoder


class RGBMLDecoder(_BaseMLDecoder):
    """
    ML decoder for RGB-encoded QR codes.
    
    Outputs 3 binary layers corresponding to R, G, B channels.
    """
    
    def __init__(self, device: str | None = None):
        super().__init__(num_outputs=3, device=device)
    
    def train_epoch(
        self,
        num_samples: int = 100,
        batch_size: int = 8,
        version: int = 1,
    ) -> float:
        """Train for one epoch using generated RGB data."""
        self.model.train()
        total_loss = 0.0
        num_batches = (num_samples + batch_size - 1) // batch_size

        for _ in range(num_batches):
            images, labels = _generate_rgb_batch(batch_size, version)

            x = torch.from_numpy(images.transpose(0, 3, 1, 2)).float().to(self.device) / 255.0
            y = torch.from_numpy(labels.transpose(0, 3, 1, 2)).float().to(self.device)

            self.optimizer.zero_grad()
            output = self.model(x)
            loss = self.criterion(output, y)
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

        return total_loss / num_batches
    
    def decode(self, img: Image.Image) -> List[str]:
        """Decode an RGB QR code into 3 strings."""
        import cv2
        
        layers = self.predict_layers(img)
        
        results = []
        for i in range(3):
            layer = layers[:, :, i]
            binary = ((1 - layer) * 255).astype(np.uint8)
            
            # Try OpenCV first
            detector = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(binary)
            
            if not data:
                # Fallback to pyzbar
                try:
                    from pyzbar import pyzbar
                    pil_img = Image.fromarray(binary)
                    decoded = pyzbar.decode(pil_img)
                    if decoded:
                        data = decoded[0].data.decode('utf-8')
                except ImportError:
                    pass
            
            results.append(data or "")
        
        return results


class PaletteMLDecoder(_BaseMLDecoder):
    """
    ML decoder for palette-encoded QR codes.
    
    Supports 1-9 layers with automatic palette selection:
    - 1-6 layers: 64-color palette (6-bit model)
    - 7-8 layers: 256-color palette (8-bit model)
    - 9 layers: 512-color palette (9-bit model)
    
    Args:
        num_layers: Number of data layers to decode (1-9). Default is 6.
        device: Device to run on ('cuda' or 'cpu'). Auto-detected if None.
    
    Example:
        >>> decoder = PaletteMLDecoder(num_layers=6)
        >>> for epoch in range(10):
        ...     loss = decoder.train_epoch(num_samples=100)
        >>> results = decoder.decode(image)
    """
    
    def __init__(self, num_layers: int = 6, device: str | None = None):
        if num_layers < 1 or num_layers > 9:
            raise ValueError(f"num_layers must be 1-9, got {num_layers}")
        
        self.num_layers = num_layers
        self.model_bits = _num_layers_to_model_bits(num_layers)
        
        super().__init__(num_outputs=self.model_bits, device=device)
    
    def train_epoch(
        self,
        num_samples: int = 100,
        batch_size: int = 8,
        version: int = 1,
    ) -> float:
        """
        Train for one epoch using generated palette data.
        
        Training uses the full model_bits (6, 8, or 9) even if num_layers
        is less, to match the actual palette encoding.
        """
        self.model.train()
        total_loss = 0.0
        num_batches = (num_samples + batch_size - 1) // batch_size

        for _ in range(num_batches):
            # Generate training data using full model bits
            images, labels = _generate_palette_batch(
                batch_size, version, self.model_bits
            )

            x = torch.from_numpy(images.transpose(0, 3, 1, 2)).float().to(self.device) / 255.0
            y = torch.from_numpy(labels.transpose(0, 3, 1, 2)).float().to(self.device)

            self.optimizer.zero_grad()
            output = self.model(x)
            loss = self.criterion(output, y)
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

        return total_loss / num_batches
    
    def decode(self, img: Image.Image, num_layers: int | None = None) -> List[str]:
        """
        Decode a palette QR code.
        
        Args:
            img: PIL Image to decode
            num_layers: Override number of layers to return (default: use init value)
            
        Returns:
            List of decoded strings, one per layer
        """
        import cv2
        
        if num_layers is None:
            num_layers = self.num_layers
        
        # Validate requested layers don't exceed model capacity
        if num_layers > self.model_bits:
            raise ValueError(
                f"Cannot decode {num_layers} layers with a {self.model_bits}-bit model. "
                f"Create a new decoder with num_layers={num_layers}."
            )
        
        layers = self.predict_layers(img)
        
        results = []
        for i in range(num_layers):
            layer = layers[:, :, i]
            binary = ((1 - layer) * 255).astype(np.uint8)
            
            # Try OpenCV first
            detector = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(binary)
            
            if not data:
                # Fallback to pyzbar
                try:
                    from pyzbar import pyzbar
                    pil_img = Image.fromarray(binary)
                    decoded = pyzbar.decode(pil_img)
                    if decoded:
                        data = decoded[0].data.decode('utf-8')
                except ImportError:
                    pass
            
            results.append(data or "")
        
        return results


# =============================================================================
# Training Data Generation
# =============================================================================

# Layer cache for fast training data generation
_LAYER_CACHE: dict[tuple[int, int], list[np.ndarray]] = {}
_LAYER_CACHE_SIZE = 100  # Number of pre-generated layers per (version, size)


def _get_cached_layers(version: int, num_needed: int, use_cache: bool = True) -> list[np.ndarray]:
    """
    Get random layers, optionally from cache.
    
    Args:
        version: QR code version
        num_needed: Number of layers to return
        use_cache: If True, use cached layers (fast). If False, generate fresh (slow but more diverse).
    """
    from .encoder import _make_layer
    import random
    import string
    
    if not use_cache:
        # Generate fresh layers (slow but more diverse)
        layers = []
        for _ in range(num_needed):
            length = random.randint(3, 8)
            data = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            layer = _make_layer(data, version, "M")
            layers.append(layer)
        return layers
    
    # Generate a test layer to get dimensions
    test_layer = _make_layer("A", version, "M")
    cache_key = (version, test_layer.shape[0])  # (version, size)
    
    # Build cache if not exists
    if cache_key not in _LAYER_CACHE or len(_LAYER_CACHE[cache_key]) < _LAYER_CACHE_SIZE:
        layers = []
        for _ in range(_LAYER_CACHE_SIZE):
            length = random.randint(3, 8)
            data = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            layer = _make_layer(data, version, "M")
            layers.append(layer)
        _LAYER_CACHE[cache_key] = layers
    
    # Return random selection from cache
    return random.choices(_LAYER_CACHE[cache_key], k=num_needed)


def _generate_rgb_sample(version: int = 1, use_cache: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """Generate a single RGB training sample.
    
    Matches the actual encode_rgb behavior:
    - channel = layer * 255
    - So black modules (layer=1) become bright (255)
    - White areas (layer=0) become dark (0)
    
    Args:
        version: QR code version
        use_cache: If True, use cached layers (fast). If False, generate fresh.
    """
    # Get 3 random layers from cache
    layers = _get_cached_layers(version, 3, use_cache=use_cache)
    h, w = layers[0].shape
    
    # Build RGB image matching encode_rgb: channel = layer * 255
    image = np.zeros((h, w, 3), dtype=np.uint8)
    labels = np.zeros((h, w, 3), dtype=np.uint8)
    
    for c in range(3):
        image[:, :, c] = layers[c] * 255
        labels[:, :, c] = layers[c]
    
    return image, labels


def _generate_rgb_batch(
    batch_size: int = 8,
    version: int = 1,
    use_cache: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate a batch of RGB training samples."""
    samples = [_generate_rgb_sample(version, use_cache=use_cache) for _ in range(batch_size)]
    images = np.stack([s[0] for s in samples])
    labels = np.stack([s[1] for s in samples])
    return images, labels


# Pre-built lookup tables for vectorized palette sample generation
_PALETTE_LUT_6: np.ndarray | None = None
_PALETTE_LUT_8: np.ndarray | None = None
_PALETTE_LUT_9: np.ndarray | None = None


def _get_palette_lut(num_bits: int) -> np.ndarray:
    """
    Get or build a lookup table for palette colors.
    
    The LUT maps integer indices (0 to 2^num_bits - 1) to RGB colors.
    Index is computed as: sum(bit[i] * 2^i for i in range(num_bits))
    """
    global _PALETTE_LUT_6, _PALETTE_LUT_8, _PALETTE_LUT_9
    
    from .palette import palette_6, palette_8, palette_9
    
    if num_bits == 6:
        if _PALETTE_LUT_6 is None:
            codebook = palette_6()
            lut = np.zeros((64, 3), dtype=np.uint8)
            for bits, color in codebook.items():
                idx = sum(b * (2 ** i) for i, b in enumerate(bits))
                lut[idx] = color
            _PALETTE_LUT_6 = lut
        return _PALETTE_LUT_6
    elif num_bits == 8:
        if _PALETTE_LUT_8 is None:
            codebook = palette_8()
            lut = np.zeros((256, 3), dtype=np.uint8)
            for bits, color in codebook.items():
                idx = sum(b * (2 ** i) for i, b in enumerate(bits))
                lut[idx] = color
            _PALETTE_LUT_8 = lut
        return _PALETTE_LUT_8
    else:  # num_bits == 9
        if _PALETTE_LUT_9 is None:
            codebook = palette_9()
            lut = np.zeros((512, 3), dtype=np.uint8)
            for bits, color in codebook.items():
                idx = sum(b * (2 ** i) for i, b in enumerate(bits))
                lut[idx] = color
            _PALETTE_LUT_9 = lut
        return _PALETTE_LUT_9


def _generate_palette_sample(
    version: int = 1,
    num_layers: int = 6,
    use_cache: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a single palette training sample (vectorized).
    
    Args:
        version: QR code version
        num_layers: Number of bits/layers (6, 8, or 9)
        use_cache: If True, use cached layers (fast). If False, generate fresh.
        
    Returns:
        (image, labels) tuple where labels has shape (h, w, num_layers)
    """
    # Select appropriate bit depth
    if num_layers <= 6:
        num_bits = 6
    elif num_layers <= 8:
        num_bits = 8
    else:
        num_bits = 9

    # Get random layers from cache
    layers = _get_cached_layers(version, num_bits, use_cache=use_cache)
    h, w = layers[0].shape
    labels = np.stack(layers, axis=-1).astype(np.uint8)  # (h, w, num_bits)

    # Compute index for each pixel: sum(bit[i] * 2^i)
    powers = 2 ** np.arange(num_bits, dtype=np.uint32)
    indices = np.tensordot(labels, powers, axes=([-1], [0])).astype(np.uint32)

    # Look up colors using the precomputed LUT
    lut = _get_palette_lut(num_bits)
    image = lut[indices]  # (h, w, 3)

    return image, labels


def _generate_palette_batch(
    batch_size: int = 8,
    version: int = 1,
    num_layers: int = 6,
    use_cache: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate a batch of palette training samples."""
    samples = [_generate_palette_sample(version, num_layers, use_cache=use_cache) for _ in range(batch_size)]
    images = np.stack([s[0] for s in samples])
    labels = np.stack([s[1] for s in samples])
    return images, labels


# =============================================================================
# Legacy API (for backward compatibility)
# =============================================================================

# Keep old names for backward compatibility
if TORCH_AVAILABLE:
    MLDecoder = PaletteMLDecoder
    ColorUnmixingCNN = LayerUnmixingCNN


def generate_training_sample(
    version: int = 1,
    num_layers: int = 6,
    mode: str = "palette",
    use_cache: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """Legacy function - generate training sample."""
    if mode == "rgb":
        return _generate_rgb_sample(version, use_cache=use_cache)
    else:
        return _generate_palette_sample(version, num_layers, use_cache=use_cache)


def generate_training_batch(
    batch_size: int = 8,
    version: int = 1,
    num_layers: int = 6,
    mode: str = "palette",
    use_cache: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """Legacy function - generate training batch."""
    if mode == "rgb":
        return _generate_rgb_batch(batch_size, version, use_cache=use_cache)
    else:
        return _generate_palette_batch(batch_size, version, num_layers, use_cache=use_cache)


def decode_rgb_ml(
    img: Image.Image,
    decoder: RGBMLDecoder | PaletteMLDecoder | None = None,
) -> List[str]:
    """
    Decode an RGB QR code using ML-based layer separation.
    
    For best results, use a trained RGBMLDecoder.
    """
    if decoder is None:
        decoder = RGBMLDecoder()
    
    if isinstance(decoder, RGBMLDecoder):
        return decoder.decode(img)
    else:
        # Legacy: using PaletteMLDecoder for RGB (not recommended)
        layers = decoder.predict_layers(img)
        import cv2
        results = []
        for i in range(3):
            layer = layers[:, :, i]
            binary = ((1 - layer) * 255).astype(np.uint8)
            detector = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(binary)
            results.append(data or "")
        return results


def decode_layers_ml(
    img: Image.Image,
    num_layers: int = 6,
    decoder: PaletteMLDecoder | None = None,
) -> List[str]:
    """
    Decode palette-encoded QR code using ML-based layer separation.
    
    For best results, use a trained PaletteMLDecoder with matching num_layers.
    """
    if decoder is None:
        decoder = PaletteMLDecoder(num_layers=num_layers)
    
    return decoder.decode(img, num_layers=num_layers)
