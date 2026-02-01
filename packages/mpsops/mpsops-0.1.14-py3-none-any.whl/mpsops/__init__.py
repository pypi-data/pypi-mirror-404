"""
MPS Ops - CUDA-only PyTorch operations for Apple Silicon

A collection of Metal implementations for operations that are typically CUDA-only.
Install this metapackage to get all mpsops packages at once.

Packages included:
- mps-flash-attn: Flash attention for transformers
- mps-bitsandbytes: Quantized operations (8-bit, 4-bit)
- mps-deform-conv: Deformable convolution for detection
- mps-correlation: Correlation for optical flow
- mps-carafe: Content-aware upsampling
- mps-conv3d: 3D convolution for video models
"""

__version__ = "0.1.1"

# Re-export from subpackages for convenience
try:
    from mps_flash_attn import flash_attn_func, flash_attn_qkvpacked_func
except ImportError:
    flash_attn_func = None
    flash_attn_qkvpacked_func = None

try:
    from mps_bitsandbytes import Linear8bitLt, Linear4bit
except ImportError:
    Linear8bitLt = None
    Linear4bit = None

try:
    from mps_deform_conv import deform_conv2d, DeformConv2d
except ImportError:
    deform_conv2d = None
    DeformConv2d = None

try:
    from mps_correlation import correlation, Correlation, CorrBlock
except ImportError:
    correlation = None
    Correlation = None
    CorrBlock = None

try:
    from mps_carafe import carafe, CARAFE, CARAFEPack
except ImportError:
    carafe = None
    CARAFE = None
    CARAFEPack = None

try:
    from mps_conv3d import conv3d, Conv3d, patch_conv3d
except ImportError:
    conv3d = None
    Conv3d = None
    patch_conv3d = None


def available_packages():
    """Return a dict of available packages and their status."""
    packages = {
        "mps-flash-attn": flash_attn_func is not None,
        "mps-bitsandbytes": Linear8bitLt is not None,
        "mps-deform-conv": deform_conv2d is not None,
        "mps-correlation": correlation is not None,
        "mps-carafe": carafe is not None,
        "mps-conv3d": conv3d is not None,
    }
    return packages


def print_status():
    """Print the status of all mpsops packages."""
    print("MPS Ops Package Status:")
    print("-" * 40)
    for name, available in available_packages().items():
        status = "✓ installed" if available else "✗ not installed"
        print(f"  {name}: {status}")
