# MPS Correlation

Correlation layer for optical flow on Apple Silicon (M1/M2/M3/M4).

**Drop-in replacement** for `spatial-correlation-sampler` and mmcv's correlation op.

## Why?

Correlation layers are essential for optical flow estimation:
- **RAFT**: State-of-the-art optical flow
- **PWC-Net**: Efficient optical flow
- **FlowNet/FlowNet2**: Classic deep optical flow

But existing implementations are **CUDA-only**. On Mac you get:
```
NotImplementedError: correlation not implemented for MPS
```

This package provides a native Metal implementation.

## Installation

```bash
pip install mps-correlation
```

Or from source:

```bash
git clone https://github.com/mpsops/mps-correlation
cd mps-correlation
pip install -e .
```

## Quick Start

### Basic Usage

```python
import torch
from mps_correlation import correlation

# Two feature maps from consecutive frames
fmap1 = torch.randn(1, 256, 64, 64, device='mps')
fmap2 = torch.randn(1, 256, 64, 64, device='mps')

# Compute correlation volume
corr = correlation(
    fmap1, fmap2,
    kernel_size=1,
    max_displacement=4,
    stride1=1,
    stride2=1,
    pad_size=4
)
# Output: (1, 81, 64, 64) - 81 = (2*4+1)^2 displacement channels
```

### Correlation Module

```python
from mps_correlation import Correlation

corr_layer = Correlation(
    kernel_size=1,
    max_displacement=4,
    stride1=1,
    stride2=1,
    pad_size=4
)

corr = corr_layer(fmap1, fmap2)
```

### RAFT-style All-Pairs Correlation

```python
from mps_correlation import CorrBlock

# Build correlation pyramid
corr_block = CorrBlock(fmap1, fmap2, num_levels=4, radius=4)

# Lookup at specific coordinates
coords = torch.zeros(1, 2, 64, 64, device='mps')  # (x, y) coordinates
corr_features = corr_block(coords)
```

## API Reference

### `correlation(input1, input2, kernel_size, max_displacement, stride1, stride2, pad_size, is_multiply)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `input1` | Tensor | First feature map (N, C, H, W) |
| `input2` | Tensor | Second feature map (N, C, H, W) |
| `kernel_size` | int | Size of correlation kernel (default: 1) |
| `max_displacement` | int | Maximum displacement to search (default: 4) |
| `stride1` | int | Stride for input1 (default: 1) |
| `stride2` | int | Stride for displacement (default: 1) |
| `pad_size` | int | Padding size (default: 4) |
| `is_multiply` | bool | Use multiplication (True) or subtraction (False) |

### `CorrBlock`

RAFT-style correlation block with pyramid and lookup.

## How It Works

Correlation computes similarity between patches at different displacements:

```
For each position (x, y) in output:
    For each displacement (dx, dy) in [-max_disp, max_disp]:
        corr[x, y, dx, dy] = sum(fmap1[x, y, :] * fmap2[x+dx, y+dy, :])
```

This creates a 4D cost volume that optical flow networks use to estimate motion.

## Compatibility

- **PyTorch**: 2.0+
- **macOS**: 12.0+ (Monterey)
- **Hardware**: Apple Silicon (M1/M2/M3/M4)

## Features

- Full forward and backward pass (training supported)
- fp32 and fp16 supported
- Compatible with RAFT, PWC-Net, FlowNet architectures

## Credits

- [spatial-correlation-sampler](https://github.com/ClementPinard/Pytorch-Correlation-extension) - Reference implementation
- [RAFT](https://github.com/princeton-vl/RAFT) - State-of-the-art optical flow
- [PWC-Net](https://github.com/NVlabs/PWC-Net) - Efficient optical flow

## License

MIT
