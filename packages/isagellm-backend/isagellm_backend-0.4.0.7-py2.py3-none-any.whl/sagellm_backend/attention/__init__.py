"""Attention backend interfaces and implementations.

This module provides:
- AttentionBackend: Base class for attention implementations
- CPUAttentionBackend: CPU-based attention
- AttentionMetadata: Metadata for attention computation

The attention backend abstracts hardware-specific attention implementations:
- Flash Attention (CUDA)
- PagedAttention (CUDA, vLLM style)
- Vanilla attention (CPU)
- ACL attention (Ascend)

Example:
    attn_backend = backend.get_attention_backend()
    output = attn_backend.forward(query, key, value, attn_metadata)
"""

from __future__ import annotations

from sagellm_backend.attention.base import AttentionBackend, AttentionMetadata
from sagellm_backend.attention.cpu import CPUAttentionBackend

__all__ = [
    "AttentionBackend",
    "AttentionMetadata",
    "CPUAttentionBackend",
]
