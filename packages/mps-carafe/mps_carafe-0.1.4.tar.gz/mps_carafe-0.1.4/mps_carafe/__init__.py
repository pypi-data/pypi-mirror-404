"""
MPS CARAFE - Content-Aware ReAssembly of FEatures for Apple Silicon

Drop-in replacement for mmcv's CARAFE op.
Used in Mask R-CNN, FPN, and other detection/segmentation networks.
"""

import torch
from torch import nn, Tensor
from torch.autograd import Function
from typing import Tuple

__version__ = "0.1.2"


def _load_library():
    """Load the native extension."""
    try:
        from mps_carafe import _C as _lib
        return _lib
    except ImportError:
        import os
        from torch.utils.cpp_extension import load

        src_dir = os.path.join(os.path.dirname(__file__), "csrc")
        _lib = load(
            name="mps_carafe",
            sources=[os.path.join(src_dir, "carafe_mps.mm")],
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


class _CARAFEFunction(Function):
    """Autograd function for CARAFE."""

    @staticmethod
    def forward(
        ctx,
        features: Tensor,
        masks: Tensor,
        kernel_size: int,
        group_size: int,
        scale_factor: int,
    ) -> Tensor:
        ctx.save_for_backward(features, masks)
        ctx.kernel_size = kernel_size
        ctx.group_size = group_size
        ctx.scale_factor = scale_factor

        lib = _get_lib()
        output = lib.carafe_forward(
            features, masks,
            kernel_size, group_size, scale_factor
        )
        return output

    @staticmethod
    def backward(ctx, grad_output: Tensor):
        features, masks = ctx.saved_tensors
        lib = _get_lib()

        grad_features, grad_masks = lib.carafe_backward(
            grad_output.contiguous(),
            features.contiguous(),
            masks.contiguous(),
            ctx.kernel_size,
            ctx.group_size,
            ctx.scale_factor
        )

        return grad_features, grad_masks, None, None, None


def carafe(
    features: Tensor,
    masks: Tensor,
    kernel_size: int,
    group_size: int,
    scale_factor: int,
) -> Tensor:
    """
    CARAFE: Content-Aware ReAssembly of FEatures.

    Performs content-aware upsampling using learned reassembly kernels.

    Args:
        features: Input feature map (N, C, H, W)
        masks: Reassembly kernels (N, group_size * kernel_size^2, H*scale, W*scale)
        kernel_size: Size of the reassembly kernel (typically 5)
        group_size: Number of groups for channel-wise reassembly
        scale_factor: Upsampling factor (typically 2)

    Returns:
        Upsampled feature map (N, C, H*scale_factor, W*scale_factor)
    """
    if features.device.type != "mps":
        raise ValueError(f"Input must be on MPS device, got {features.device}")

    return _CARAFEFunction.apply(
        features, masks,
        kernel_size, group_size, scale_factor
    )


class CARAFE(nn.Module):
    """
    CARAFE: Content-Aware ReAssembly of FEatures.

    A learnable upsampling operator that uses content-aware kernels
    for feature reassembly. Better than bilinear/nearest for dense prediction.

    Args:
        kernel_size: Size of reassembly kernel (default: 5)
        group_size: Number of channel groups (default: 1)
        scale_factor: Upsampling factor (default: 2)
    """

    def __init__(
        self,
        kernel_size: int = 5,
        group_size: int = 1,
        scale_factor: int = 2,
    ):
        super().__init__()
        self.kernel_size = kernel_size
        self.group_size = group_size
        self.scale_factor = scale_factor

    def forward(self, features: Tensor, masks: Tensor) -> Tensor:
        return carafe(
            features, masks,
            self.kernel_size, self.group_size, self.scale_factor
        )


class CARAFEPack(nn.Module):
    """
    CARAFE with built-in mask predictor.

    This module includes the convolutions to predict reassembly masks
    from input features, making it a complete upsampling block.

    Args:
        channels: Number of input/output channels
        kernel_size: Size of reassembly kernel (default: 5)
        group_size: Number of channel groups (default: 1)
        scale_factor: Upsampling factor (default: 2)
        compressed_channels: Channels after compression (default: 64)
    """

    def __init__(
        self,
        channels: int,
        kernel_size: int = 5,
        group_size: int = 1,
        scale_factor: int = 2,
        compressed_channels: int = 64,
    ):
        super().__init__()
        self.channels = channels
        self.kernel_size = kernel_size
        self.group_size = group_size
        self.scale_factor = scale_factor

        # Channel compressor
        self.channel_compressor = nn.Conv2d(
            channels, compressed_channels, kernel_size=1
        )

        # Content encoder - predicts reassembly masks
        self.content_encoder = nn.Conv2d(
            compressed_channels,
            group_size * kernel_size * kernel_size * scale_factor * scale_factor,
            kernel_size=3,
            padding=1,
        )

        # CARAFE operator
        self.carafe = CARAFE(kernel_size, group_size, scale_factor)

    def forward(self, x: Tensor) -> Tensor:
        # Compress channels
        compressed = self.channel_compressor(x)

        # Predict masks
        masks = self.content_encoder(compressed)

        # Upsample masks to output resolution
        n, _, h, w = masks.shape
        masks = masks.view(n, self.group_size, self.kernel_size * self.kernel_size,
                          self.scale_factor, self.scale_factor, h, w)
        masks = masks.permute(0, 1, 2, 5, 3, 6, 4).contiguous()
        masks = masks.view(n, self.group_size * self.kernel_size * self.kernel_size,
                          h * self.scale_factor, w * self.scale_factor)

        # Softmax over kernel positions
        masks = torch.softmax(masks.view(n, self.group_size, -1,
                                         h * self.scale_factor, w * self.scale_factor), dim=2)
        masks = masks.view(n, -1, h * self.scale_factor, w * self.scale_factor)

        # Apply CARAFE
        return self.carafe(x, masks)


def is_available() -> bool:
    """Check if MPS is available."""
    return torch.backends.mps.is_available()
