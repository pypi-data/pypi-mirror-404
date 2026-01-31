"""sageLLM Backend Provider 抽象。

本包提供硬件后端抽象层：
- BackendProvider 接口定义
- Stream/Event/KVBlock 抽象
- get_provider() 工厂函数 - 推荐的获取 Provider 方式
- Kernel 接口和实现（Linear, Embedding, RMSNorm, SiLU 等）
- AttentionBackend 接口和实现
- CPU Backend 实现
- CUDA Backend 实现 (PyTorch)
- Ascend Backend 实现 (PyTorch-NPU)

推荐使用方式 (vLLM v1 style):
    from sagellm_backend import get_provider

    # 自动选择最佳可用后端
    provider = get_provider()

    # 显式指定后端
    provider = get_provider("cuda")
    provider = get_provider("cpu")
    provider = get_provider("ascend")

    # 获取 Kernel
    linear_kernel = provider.get_kernel("linear")
    output = linear_kernel(input, weight)

    # 获取 Attention Backend
    attn_backend = provider.get_attention_backend()
    output = attn_backend.forward(query, key, value, attn_metadata)

能力描述符（DType, KernelKind, CapabilityDescriptor）已迁移至 sagellm-protocol。
请直接从 sagellm_protocol 导入这些类型。

Note: Engine implementations have been moved to sagellm-core.
      This package now focuses solely on hardware abstraction.
"""

from __future__ import annotations

__version__ = "0.4.0.7"

from sagellm_protocol import CapabilityDescriptor, DType, KernelKind

# Attention backend interfaces
from sagellm_backend.attention.base import AttentionBackend, AttentionMetadata
from sagellm_backend.attention.cpu import CPUAttentionBackend
from sagellm_backend.base import BackendProvider, Event, KVBlock, Stream
from sagellm_backend.kernels.activation import CPUSiLUKernel, GELUKernel, ReLUKernel, SiLUKernel

# Kernel interfaces
from sagellm_backend.kernels.base import Kernel, KernelRegistry
from sagellm_backend.kernels.embedding import CPUEmbeddingKernel, EmbeddingKernel
from sagellm_backend.kernels.linear import CPULinearKernel, LinearKernel
from sagellm_backend.kernels.normalization import CPURMSNormKernel, LayerNormKernel, RMSNormKernel

# Memory management
from sagellm_backend.memory import (
    MemoryAllocator,
    MemoryHandle,
    MemoryPool,
    pin_memory,
    unpin_memory,
)
from sagellm_backend.providers.cpu import CPUBackendProvider, create_cpu_backend

# Provider Registry and factory function (vLLM v1 style)
from sagellm_backend.registry import (
    get_provider,
    is_provider_available,
    list_providers,
    register_provider,
)

# Optional PyTorch-based providers (lazy import)
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

__version__ = "0.4.0.7"

__all__ = [
    # Version
    "__version__",
    # =========================================================================
    # Provider Registry (vLLM v1 style) - RECOMMENDED
    # =========================================================================
    "get_provider",  # Factory function to get BackendProvider
    "register_provider",  # Register custom provider
    "list_providers",  # List available providers
    "is_provider_available",  # Check if provider is available
    # =========================================================================
    # Provider interface
    # =========================================================================
    "BackendProvider",
    "Stream",
    "Event",
    "KVBlock",
    # Capability types (re-exported from protocol for convenience)
    "CapabilityDescriptor",
    "DType",
    "KernelKind",
    # =========================================================================
    # Kernel interfaces
    # =========================================================================
    "Kernel",
    "KernelRegistry",
    "LinearKernel",
    "CPULinearKernel",
    "EmbeddingKernel",
    "CPUEmbeddingKernel",
    "RMSNormKernel",
    "CPURMSNormKernel",
    "LayerNormKernel",
    "SiLUKernel",
    "CPUSiLUKernel",
    "GELUKernel",
    "ReLUKernel",
    # =========================================================================
    # Attention backend interfaces
    # =========================================================================
    "AttentionBackend",
    "AttentionMetadata",
    "CPUAttentionBackend",
    # =========================================================================
    # Memory Management
    # =========================================================================
    "MemoryAllocator",
    "MemoryHandle",
    "MemoryPool",
    "pin_memory",
    "unpin_memory",
    # =========================================================================
    # Provider implementations
    # =========================================================================
    # CPU backend implementation
    "CPUBackendProvider",
    "create_cpu_backend",
    # PyTorch CUDA backend (optional)
    "PyTorchCUDABackendProvider",
    "create_pytorch_cuda_backend",
    # PyTorch Ascend backend (optional)
    "PyTorchAscendBackendProvider",
    "create_pytorch_ascend_backend",
]
