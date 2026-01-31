# MPS Ops

**CUDA-only PyTorch operations for Apple Silicon.**

This metapackage installs all mpsops packages - Metal implementations of operations that are typically CUDA-only.

## Installation

Install everything:
```bash
pip install mpsops
```

Or install individual packages:
```bash
pip install mps-flash-attn    # Flash attention
pip install mps-bitsandbytes  # Quantized ops
pip install mps-deform-conv   # Deformable convolution
pip install mps-correlation   # Optical flow correlation
pip install mps-carafe        # Content-aware upsampling
pip install mps-conv3d        # 3D convolution for video
```

## Packages

| Package | Description | Use Case |
|---------|-------------|----------|
| [mps-flash-attn](https://github.com/mpsops/mps-flash-attn) | Flash Attention | Transformers, LLMs |
| [mps-bitsandbytes](https://github.com/mpsops/mps-bitsandbytes) | NF4/FP4/FP8/INT8 quantization | LLM inference, QLoRA |
| [mps-deform-conv](https://github.com/mpsops/mps-deform-conv) | Deformable convolution | Object detection (DETR, DCN) |
| [mps-correlation](https://github.com/mpsops/mps-correlation) | Correlation layer | Optical flow (RAFT, PWC-Net) |
| [mps-carafe](https://github.com/mpsops/mps-carafe) | CARAFE upsampling | Segmentation (Mask R-CNN) |
| [mps-conv3d](https://github.com/mpsops/mps-conv3d) | 3D Convolution | Video models (I3D, SlowFast, MMAudio) |

## Quick Start

```python
import mpsops

# Check what's installed
mpsops.print_status()

# Use the ops directly
from mpsops import flash_attn_func, deform_conv2d, correlation, carafe, conv3d, patch_conv3d
```

## Compatibility

- **PyTorch**: 2.0+
- **macOS**: 12.0+ (Monterey)
- **Hardware**: Apple Silicon (M1/M2/M3/M4)

## Why?

Many state-of-the-art models use CUDA-only operations:
- **LLMs** need flash attention and quantization
- **Object detection** needs deformable convolution
- **Optical flow** needs correlation layers
- **Segmentation** needs specialized upsampling

On Mac, you get errors like:
```
NotImplementedError: flash_attn not implemented for MPS
```

MPS Ops provides native Metal implementations so these models run on Apple Silicon.

## License

MIT
