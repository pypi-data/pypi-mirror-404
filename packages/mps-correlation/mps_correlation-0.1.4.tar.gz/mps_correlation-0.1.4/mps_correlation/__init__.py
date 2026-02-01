"""
MPS Correlation - Optical flow correlation layer for Apple Silicon

Drop-in replacement for spatial-correlation-sampler and mmcv's correlation op.
Used in RAFT, PWC-Net, FlowNet, etc.
"""

import torch
from torch import nn, Tensor
from torch.autograd import Function
from typing import Optional, Tuple
import math

__version__ = "0.1.2"


def _load_library():
    """Load the native extension."""
    try:
        from mps_correlation import _C as _lib
        return _lib
    except ImportError:
        import os
        from torch.utils.cpp_extension import load

        src_dir = os.path.join(os.path.dirname(__file__), "csrc")
        _lib = load(
            name="mps_correlation",
            sources=[os.path.join(src_dir, "correlation_mps.mm")],
            extra_cflags=["-std=c++17"],
            extra_ldflags=["-framework", "Metal", "-framework", "Foundation"],
            verbose=False,
        )
        return _lib


_lib_cache = None


def _get_lib():
    global _lib_cache
    if _lib_cache is None:
        _lib_cache = _load_library()
    return _lib_cache


class _CorrelationFunction(Function):
    """Autograd function for correlation."""

    @staticmethod
    def forward(
        ctx,
        input1: Tensor,
        input2: Tensor,
        kernel_size: int,
        max_displacement: int,
        stride1: int,
        stride2: int,
        pad_size: int,
        is_multiply: bool,
    ) -> Tensor:
        ctx.save_for_backward(input1, input2)
        ctx.kernel_size = kernel_size
        ctx.max_displacement = max_displacement
        ctx.stride1 = stride1
        ctx.stride2 = stride2
        ctx.pad_size = pad_size
        ctx.is_multiply = is_multiply

        lib = _get_lib()
        output = lib.correlation_forward(
            input1, input2,
            kernel_size, max_displacement,
            stride1, stride2, pad_size,
            is_multiply
        )
        return output

    @staticmethod
    def backward(ctx, grad_output: Tensor):
        input1, input2 = ctx.saved_tensors
        lib = _get_lib()

        grad_input1, grad_input2 = lib.correlation_backward(
            grad_output.contiguous(), input1.contiguous(), input2.contiguous(),
            ctx.kernel_size, ctx.max_displacement,
            ctx.stride1, ctx.stride2, ctx.pad_size,
            ctx.is_multiply
        )

        return grad_input1, grad_input2, None, None, None, None, None, None


def correlation(
    input1: Tensor,
    input2: Tensor,
    kernel_size: int = 1,
    max_displacement: int = 4,
    stride1: int = 1,
    stride2: int = 1,
    pad_size: int = 4,
    is_multiply: bool = True,
) -> Tensor:
    """
    Compute correlation between two feature maps.

    Used in optical flow estimation (RAFT, PWC-Net, FlowNet).

    Args:
        input1: First feature map (N, C, H, W)
        input2: Second feature map (N, C, H, W)
        kernel_size: Size of the correlation kernel
        max_displacement: Maximum displacement for correlation search
        stride1: Stride for input1
        stride2: Stride for input2 (displacement stride)
        pad_size: Padding size
        is_multiply: If True, use multiplication. If False, use subtraction.

    Returns:
        Correlation volume (N, D*D, H, W) where D = 2*max_displacement/stride2 + 1
    """
    if input1.device.type != "mps":
        raise ValueError(f"Input must be on MPS device, got {input1.device}")

    return _CorrelationFunction.apply(
        input1, input2,
        kernel_size, max_displacement,
        stride1, stride2, pad_size,
        is_multiply
    )


class Correlation(nn.Module):
    """
    Correlation layer for optical flow.

    Computes a cost volume by correlating features from two images.

    Args:
        kernel_size: Size of correlation kernel
        max_displacement: Maximum displacement to search
        stride1: Stride for first input
        stride2: Stride for displacement
        pad_size: Padding size
        is_multiply: Use multiplication (True) or subtraction (False)
    """

    def __init__(
        self,
        kernel_size: int = 1,
        max_displacement: int = 4,
        stride1: int = 1,
        stride2: int = 1,
        pad_size: int = 4,
        is_multiply: bool = True,
    ):
        super().__init__()
        self.kernel_size = kernel_size
        self.max_displacement = max_displacement
        self.stride1 = stride1
        self.stride2 = stride2
        self.pad_size = pad_size
        self.is_multiply = is_multiply

    def forward(self, input1: Tensor, input2: Tensor) -> Tensor:
        return correlation(
            input1, input2,
            self.kernel_size, self.max_displacement,
            self.stride1, self.stride2, self.pad_size,
            self.is_multiply
        )


# RAFT-style correlation (all-pairs)
class CorrBlock:
    """
    RAFT-style correlation block.

    Computes all-pairs correlation and provides lookup functionality.
    """

    def __init__(self, fmap1: Tensor, fmap2: Tensor, num_levels: int = 4, radius: int = 4):
        self.num_levels = num_levels
        self.radius = radius
        self.corr_pyramid = []

        # All-pairs correlation
        batch, dim, ht, wd = fmap1.shape
        fmap1 = fmap1.view(batch, dim, ht * wd)
        fmap2 = fmap2.view(batch, dim, ht * wd)

        corr = torch.matmul(fmap1.transpose(1, 2), fmap2)
        corr = corr.view(batch, ht, wd, 1, ht, wd)
        corr = corr / torch.sqrt(torch.tensor(dim, dtype=torch.float32, device=fmap1.device))

        self.corr_pyramid.append(corr)
        for _ in range(num_levels - 1):
            # Get current spatial dims from last two dimensions
            curr_h, curr_w = corr.shape[-2], corr.shape[-1]
            corr = torch.nn.functional.avg_pool2d(
                corr.view(batch * ht * wd, 1, curr_h, curr_w),
                kernel_size=2, stride=2
            )
            _, _, h, w = corr.shape
            corr = corr.view(batch, ht, wd, 1, h, w)
            self.corr_pyramid.append(corr)

    def __call__(self, coords: Tensor) -> Tensor:
        """Lookup correlation values at given coordinates."""
        r = self.radius
        batch, _, ht, wd = coords.shape
        coords = coords.permute(0, 2, 3, 1)

        out_pyramid = []
        for i, corr in enumerate(self.corr_pyramid):
            # Build lookup grid
            dx = torch.linspace(-r, r, 2*r+1, device=coords.device)
            dy = torch.linspace(-r, r, 2*r+1, device=coords.device)
            delta = torch.stack(torch.meshgrid(dy, dx, indexing='ij'), dim=-1)

            centroid_lvl = coords.reshape(batch * ht * wd, 1, 1, 2) / 2**i
            delta_lvl = delta.view(1, 2*r+1, 2*r+1, 2)
            coords_lvl = centroid_lvl + delta_lvl

            # Sample from correlation volume
            corr_lvl = corr.view(batch * ht * wd, 1, *corr.shape[-2:])

            # Normalize coords to [-1, 1]
            _, _, h, w = corr_lvl.shape
            coords_lvl[..., 0] = 2 * coords_lvl[..., 0] / (w - 1) - 1
            coords_lvl[..., 1] = 2 * coords_lvl[..., 1] / (h - 1) - 1

            corr_lvl = torch.nn.functional.grid_sample(
                corr_lvl, coords_lvl,
                align_corners=True, mode='bilinear', padding_mode='zeros'
            )
            corr_lvl = corr_lvl.view(batch, ht, wd, -1)
            out_pyramid.append(corr_lvl)

        out = torch.cat(out_pyramid, dim=-1)
        return out.permute(0, 3, 1, 2).contiguous()


def is_available() -> bool:
    """Check if MPS is available."""
    return torch.backends.mps.is_available()
