"""Kernel interfaces and implementations.

This module provides:
- Kernel: Base class for all kernels
- LinearKernel: Matrix multiplication kernel
- EmbeddingKernel: Token embedding kernel
- RMSNormKernel: RMS normalization kernel
- SiLUKernel: SiLU activation kernel

Kernels abstract hardware-specific compute operations, allowing
core to be hardware-agnostic.

Example:
    linear_kernel = backend.get_kernel("linear")
    output = linear_kernel(input, weight)
"""

from __future__ import annotations

from sagellm_backend.kernels.activation import SiLUKernel
from sagellm_backend.kernels.base import Kernel, KernelRegistry
from sagellm_backend.kernels.embedding import EmbeddingKernel
from sagellm_backend.kernels.linear import LinearKernel
from sagellm_backend.kernels.normalization import RMSNormKernel

__all__ = [
    "Kernel",
    "KernelRegistry",
    "LinearKernel",
    "EmbeddingKernel",
    "RMSNormKernel",
    "SiLUKernel",
]
