"""Tests for CPUBackendProvider."""

from __future__ import annotations

import pytest
from sagellm_protocol import DType

from sagellm_backend.providers.cpu import CPUBackendProvider, CPUEvent, CPUStream


class TestCPUStream:
    """Test CPU stream implementation."""

    def test_create_stream(self):
        """Test stream creation."""
        backend = CPUBackendProvider()
        stream = backend.create_stream()

        assert isinstance(stream, CPUStream)
        assert stream.stream_id == 1

    def test_stream_synchronize(self):
        """Test stream synchronization (no-op)."""
        backend = CPUBackendProvider()
        stream = backend.create_stream()

        # Should not raise
        stream.synchronize()

    def test_stream_record_event(self):
        """Test recording event in stream."""
        backend = CPUBackendProvider()
        stream = backend.create_stream()
        event = backend.create_event()

        # Should not raise
        stream.record_event(event)
        assert isinstance(event, CPUEvent)
        assert event.timestamp > 0


class TestCPUEvent:
    """Test CPU event implementation."""

    def test_create_event(self):
        """Test event creation."""
        backend = CPUBackendProvider()
        event = backend.create_event()

        assert isinstance(event, CPUEvent)
        assert event.event_id == 1

    def test_event_synchronize(self):
        """Test event synchronization (no-op)."""
        backend = CPUBackendProvider()
        event = backend.create_event()

        # Should not raise
        event.synchronize()

    def test_event_elapsed_time(self):
        """Test elapsed time calculation."""
        import time

        backend = CPUBackendProvider()
        stream = backend.create_stream()

        event1 = backend.create_event()
        stream.record_event(event1)

        time.sleep(0.01)  # 10ms

        event2 = backend.create_event()
        stream.record_event(event2)

        elapsed = event2.elapsed_ms(event1)
        assert elapsed >= 10.0
        assert elapsed < 20.0  # Should be around 10ms


class TestCPUBackendProvider:
    """Test CPUBackendProvider implementation."""

    def test_capability(self):
        """Test capability query."""
        backend = CPUBackendProvider()
        cap = backend.capability()

        assert cap.device_name == "cpu"
        assert cap.device_type == "cpu"
        assert DType.FP32 in cap.supported_dtypes
        assert cap.has_stream is True
        assert cap.has_event is True
        assert cap.has_collective is False

    def test_create_multiple_streams(self):
        """Test creating multiple streams."""
        backend = CPUBackendProvider()

        stream1 = backend.create_stream()
        stream2 = backend.create_stream()

        assert stream1.stream_id == 1
        assert stream2.stream_id == 2


class TestKVBlockManagement:
    """Test KV block management."""

    def test_kv_block_alloc(self):
        """Test KV block allocation."""
        backend = CPUBackendProvider()

        block = backend.kv_block_alloc(num_tokens=128, dtype=DType.FP16)

        assert block.handle == 1
        assert block.num_tokens == 128
        assert block.dtype == DType.FP16
        assert block.device == "cpu"

    def test_kv_block_alloc_multiple(self):
        """Test allocating multiple KV blocks."""
        backend = CPUBackendProvider()

        block1 = backend.kv_block_alloc(num_tokens=128, dtype=DType.FP16)
        block2 = backend.kv_block_alloc(num_tokens=256, dtype=DType.FP32)

        assert block1.handle == 1
        assert block2.handle == 2
        assert block1.num_tokens == 128
        assert block2.num_tokens == 256

    def test_kv_block_free(self):
        """Test KV block freeing."""
        backend = CPUBackendProvider()

        block = backend.kv_block_alloc(num_tokens=128, dtype=DType.FP16)
        backend.kv_block_free(block)

        # Should not raise when freeing again
        backend.kv_block_free(block)

    def test_kv_block_copy(self):
        """Test KV block copy (no-op)."""
        backend = CPUBackendProvider()

        src = backend.kv_block_alloc(num_tokens=128, dtype=DType.FP16)
        dst = backend.kv_block_alloc(num_tokens=128, dtype=DType.FP16)

        # Should not raise
        backend.kv_block_copy(src, dst)

    def test_kv_block_migrate_cpu_to_cpu(self):
        """Test KV block migration (CPU to CPU)."""
        backend = CPUBackendProvider()

        block = backend.kv_block_alloc(num_tokens=128, dtype=DType.FP16)
        migrated = backend.kv_block_migrate(block, "cpu")

        assert migrated.handle == block.handle
        assert migrated.device == "cpu"

    def test_kv_block_migrate_to_gpu_raises(self):
        """Test that migrating to GPU raises error."""
        backend = CPUBackendProvider()

        block = backend.kv_block_alloc(num_tokens=128, dtype=DType.FP16)

        with pytest.raises(NotImplementedError):
            backend.kv_block_migrate(block, "cuda:0")


class TestMemoryManagement:
    """Test memory management."""

    def test_memory_stats(self):
        """Test memory statistics query."""
        backend = CPUBackendProvider()
        stats = backend.memory_stats()

        assert "rss" in stats
        assert "vms" in stats
        assert "available" in stats
        assert "total" in stats
        assert "used" in stats

        # All values should be positive
        assert all(v > 0 for v in stats.values())

    def test_clear_cache(self):
        """Test cache clearing (no-op)."""
        backend = CPUBackendProvider()

        # Should not raise
        backend.clear_cache()


class TestKernelRegistry:
    """Test kernel registration."""

    def test_register_kernel(self):
        """Test kernel registration."""
        backend = CPUBackendProvider()

        def my_kernel(x, y):
            return x + y

        backend.register_kernel("add", my_kernel)

        # Should not raise
        retrieved = backend.get_kernel("add")
        assert retrieved is my_kernel

    def test_get_nonexistent_kernel_raises(self):
        """Test that getting non-existent kernel raises error."""
        backend = CPUBackendProvider()

        with pytest.raises(KeyError, match="Kernel 'nonexistent' not found"):
            backend.get_kernel("nonexistent")

    def test_kernel_execution(self):
        """Test executing registered kernel."""
        backend = CPUBackendProvider()

        def multiply(x, y):
            return x * y

        backend.register_kernel("mul", multiply)

        kernel = backend.get_kernel("mul")
        result = kernel(3, 4)
        assert result == 12


class TestCPUBackendIntegration:
    """Integration tests for CPU backend."""

    def test_stream_event_integration(self):
        """Test stream and event working together."""
        import time

        backend = CPUBackendProvider()
        stream = backend.create_stream()

        event1 = backend.create_event()
        stream.record_event(event1)

        time.sleep(0.01)

        event2 = backend.create_event()
        stream.record_event(event2)

        elapsed = event2.elapsed_ms(event1)
        assert elapsed > 0

    def test_kv_block_lifecycle(self):
        """Test complete KV block lifecycle."""
        backend = CPUBackendProvider()

        # Allocate
        block = backend.kv_block_alloc(num_tokens=256, dtype=DType.FP32)
        assert block.handle == 1

        # Copy
        block2 = backend.kv_block_alloc(num_tokens=256, dtype=DType.FP32)
        backend.kv_block_copy(block, block2)

        # Migrate
        migrated = backend.kv_block_migrate(block, "cpu")
        assert migrated.device == "cpu"

        # Free
        backend.kv_block_free(block)
        backend.kv_block_free(block2)

    def test_multiple_backends_independent(self):
        """Test that multiple backend instances are independent."""
        backend1 = CPUBackendProvider()
        backend2 = CPUBackendProvider()

        block1 = backend1.kv_block_alloc(num_tokens=128, dtype=DType.FP16)
        block2 = backend2.kv_block_alloc(num_tokens=128, dtype=DType.FP16)

        # Both should have handle=1 (independent counters)
        assert block1.handle == 1
        assert block2.handle == 1
