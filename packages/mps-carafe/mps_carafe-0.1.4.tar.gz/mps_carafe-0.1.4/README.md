# MPS CARAFE

CARAFE (Content-Aware ReAssembly of FEatures) for Apple Silicon (M1/M2/M3/M4).

**Drop-in replacement** for mmcv's CARAFE op.

## Why?

CARAFE is a learnable upsampling operator used in:
- **Mask R-CNN**: Instance segmentation
- **FPN**: Feature Pyramid Networks
- **YOLACT**: Real-time instance segmentation

But mmcv's implementation is **CUDA-only**. On Mac you get:
```
NotImplementedError: carafe not implemented for MPS
```

This package provides a native Metal implementation.

## Installation

```bash
pip install mps-carafe
```

Or from source:

```bash
git clone https://github.com/mpsops/mps-carafe
cd mps-carafe
pip install -e .
```

## Quick Start

### Basic CARAFE Operation

```python
import torch
from mps_carafe import carafe

# Input features (N, C, H, W)
features = torch.randn(1, 64, 32, 32, device='mps')

# Reassembly masks (N, group_size * k^2, H*scale, W*scale)
kernel_size = 5
group_size = 1
scale_factor = 2
masks = torch.softmax(
    torch.randn(1, group_size * kernel_size**2, 64, 64, device='mps'),
    dim=1
)

# Upsample with CARAFE
output = carafe(features, masks, kernel_size, group_size, scale_factor)
# Output: (1, 64, 64, 64)
```

### CARAFE Module

```python
from mps_carafe import CARAFE

carafe_layer = CARAFE(kernel_size=5, group_size=1, scale_factor=2)
output = carafe_layer(features, masks)
```

### CARAFEPack (with mask predictor)

```python
from mps_carafe import CARAFEPack

# Complete upsampling block with built-in mask predictor
upsample = CARAFEPack(
    channels=64,
    kernel_size=5,
    group_size=1,
    scale_factor=2
).to('mps')

output = upsample(features)  # No need to provide masks
```

## API Reference

### `carafe(features, masks, kernel_size, group_size, scale_factor)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `features` | Tensor | Input features (N, C, H, W) |
| `masks` | Tensor | Reassembly kernels (N, group_size * k^2, H*scale, W*scale) |
| `kernel_size` | int | Size of reassembly kernel (typically 5) |
| `group_size` | int | Number of channel groups (typically 1) |
| `scale_factor` | int | Upsampling factor (typically 2) |

### `CARAFEPack`

Complete CARAFE block with mask prediction convolutions.

## How It Works

CARAFE upsamples by:
1. For each output pixel, identify the corresponding input neighborhood
2. Use learned reassembly kernels (masks) to weight input pixels
3. Sum the weighted inputs to produce the output

Unlike bilinear upsampling which uses fixed weights, CARAFE learns content-aware weights that adapt to the image content.

## Compatibility

- **PyTorch**: 2.0+
- **macOS**: 12.0+ (Monterey)
- **Hardware**: Apple Silicon (M1/M2/M3/M4)

## Features

- Full forward and backward pass (training supported)
- fp32 and fp16 supported
- Compatible with mmcv CARAFE API

## Credits

- [CARAFE Paper](https://arxiv.org/abs/1905.02188) - Original research
- [mmcv](https://github.com/open-mmlab/mmcv) - Reference implementation

## License

MIT
