"""Providers 包初始化"""

from __future__ import annotations

from sagellm_backend.providers.cpu import CPUBackendProvider, create_cpu_backend
from sagellm_backend.providers.cuda import CudaBackendProvider

# PyTorch providers (optional dependencies)
try:
    from sagellm_backend.providers.pytorch_cuda import (
        PyTorchCUDABackendProvider,
        create_pytorch_cuda_backend,
    )

    _PYTORCH_CUDA_AVAILABLE = True
except ImportError:
    _PYTORCH_CUDA_AVAILABLE = False
    PyTorchCUDABackendProvider = None  # type: ignore
    create_pytorch_cuda_backend = None  # type: ignore

try:
    from sagellm_backend.providers.pytorch_ascend import (
        PyTorchAscendBackendProvider,
        create_pytorch_ascend_backend,
    )

    _PYTORCH_ASCEND_AVAILABLE = True
except ImportError:
    _PYTORCH_ASCEND_AVAILABLE = False
    PyTorchAscendBackendProvider = None  # type: ignore
    create_pytorch_ascend_backend = None  # type: ignore

__all__ = [
    "CPUBackendProvider",
    "create_cpu_backend",
    "CudaBackendProvider",
    # PyTorch providers (may be None if not installed)
    "PyTorchCUDABackendProvider",
    "create_pytorch_cuda_backend",
    "PyTorchAscendBackendProvider",
    "create_pytorch_ascend_backend",
]
