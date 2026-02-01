"""Tests for memory management module."""

from __future__ import annotations

from sagellm_protocol import DType

from sagellm_backend.memory import (
    MemoryHandle,
    MemoryPool,
    pin_memory,
    unpin_memory,
)
from sagellm_backend.memory.allocator import CPUMemoryAllocator


class TestMemoryHandle:
    """Test MemoryHandle."""

    def test_create_handle(self):
        """Test creating memory handle."""
        handle = MemoryHandle(ptr=0x1000, size_bytes=1024, dtype=DType.FP32, device="cpu")
        assert handle.ptr == 0x1000
        assert handle.size_bytes == 1024
        assert handle.dtype == DType.FP32
        assert handle.device == "cpu"

    def test_repr(self):
        """Test handle repr."""
        handle = MemoryHandle(ptr=0x1000, size_bytes=1024, dtype=DType.FP32, device="cpu")
        repr_str = repr(handle)
        assert "0x1000" in repr_str
        assert "1024" in repr_str


class TestCPUMemoryAllocator:
    """Test CPU memory allocator."""

    def test_allocate_and_free(self):
        """Test allocation and deallocation."""
        allocator = CPUMemoryAllocator()

        handle = allocator.allocate(1024, DType.FP32)
        assert handle.size_bytes == 1024
        assert handle.dtype == DType.FP32
        assert handle.device == "cpu"
        assert handle.ptr > 0

        allocator.free(handle)

    def test_allocate_tensor(self):
        """Test tensor allocation."""
        allocator = CPUMemoryAllocator()

        handle = allocator.allocate_tensor((10, 20), DType.FP32)
        # 10 * 20 * 4 bytes = 800 bytes
        assert handle.size_bytes == 800

        allocator.free(handle)

    def test_memory_info(self):
        """Test memory info."""
        allocator = CPUMemoryAllocator()

        free, total = allocator.memory_info()
        assert free > 0
        assert total > free


class TestMemoryPool:
    """Test memory pool."""

    def test_allocate_from_pool(self):
        """Test allocation from pool."""
        allocator = CPUMemoryAllocator()
        pool = MemoryPool(allocator)

        handle = pool.allocate(1024, DType.FP32)
        assert handle.size_bytes == 1024

        stats = pool.stats()
        assert stats["allocated_blocks"] == 1
        assert stats["cached_blocks"] == 0

    def test_reuse_from_pool(self):
        """Test memory reuse from pool."""
        allocator = CPUMemoryAllocator()
        pool = MemoryPool(allocator)

        # Allocate and free
        handle1 = pool.allocate(1024, DType.FP32)
        ptr1 = handle1.ptr
        pool.free(handle1)

        # Should reuse from pool
        handle2 = pool.allocate(1024, DType.FP32)
        ptr2 = handle2.ptr

        assert ptr1 == ptr2  # Same memory block reused

        stats = pool.stats()
        assert stats["cached_blocks"] == 0
        assert stats["allocated_blocks"] == 1

    def test_clear_pool(self):
        """Test clearing pool."""
        allocator = CPUMemoryAllocator()
        pool = MemoryPool(allocator)

        handle = pool.allocate(1024, DType.FP32)
        pool.free(handle)

        pool.clear()

        stats = pool.stats()
        assert stats["cached_blocks"] == 0


class TestPinMemory:
    """Test pin memory utilities."""

    def test_pin_unpin(self):
        """Test pin and unpin memory."""
        data = b"test data"

        pinned = pin_memory(data)
        assert pinned == data  # CPU-only: no-op

        unpin_memory(pinned)  # Should not raise
