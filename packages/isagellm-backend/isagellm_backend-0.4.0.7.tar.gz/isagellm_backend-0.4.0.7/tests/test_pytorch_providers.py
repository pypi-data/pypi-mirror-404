"""Tests for PyTorch Backend Providers.

Tests PyTorchCUDABackendProvider and PyTorchAscendBackendProvider interface.
Integration tests are marked with @pytest.mark.gpu and skipped by default.
"""

from __future__ import annotations

import pytest

# ============================================================================
# Interface Tests (Always Run)
# ============================================================================


class TestPyTorchCUDABackendInterface:
    """Test PyTorchCUDABackendProvider interface (no GPU required)."""

    def test_import(self):
        """Test that PyTorchCUDABackendProvider can be imported."""
        try:
            from sagellm_backend.providers.pytorch_cuda import PyTorchCUDABackendProvider

            assert PyTorchCUDABackendProvider is not None
        except ImportError:
            pytest.skip("torch not installed")

    def test_is_available(self):
        """Test is_available() class method."""
        try:
            from sagellm_backend.providers.pytorch_cuda import PyTorchCUDABackendProvider

            # Just check it returns a bool, don't check the value
            result = PyTorchCUDABackendProvider.is_available()
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("torch not installed")


class TestPyTorchAscendBackendInterface:
    """Test PyTorchAscendBackendProvider interface (no NPU required)."""

    def test_import(self):
        """Test that PyTorchAscendBackendProvider can be imported."""
        try:
            from sagellm_backend.providers.pytorch_ascend import (
                PyTorchAscendBackendProvider,
            )

            assert PyTorchAscendBackendProvider is not None
        except ImportError:
            pytest.skip("torch_npu not installed")

    def test_is_available(self):
        """Test is_available() class method."""
        try:
            from sagellm_backend.providers.pytorch_ascend import (
                PyTorchAscendBackendProvider,
            )

            # Just check it returns a bool
            result = PyTorchAscendBackendProvider.is_available()
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("torch_npu not installed")


# ============================================================================
# Integration Tests (Require Hardware - Skipped by Default)
# ============================================================================


@pytest.mark.gpu
@pytest.mark.skipif(True, reason="Requires CUDA GPU - run with --run-gpu flag")
class TestPyTorchCUDABackendIntegration:
    """Integration tests for PyTorchCUDABackendProvider (requires GPU)."""

    def test_create_backend(self):
        """Test creating backend provider."""
        from sagellm_backend.providers.pytorch_cuda import PyTorchCUDABackendProvider

        backend = PyTorchCUDABackendProvider(device_id=0)
        assert backend is not None

    def test_get_capability(self):
        """Test get_capability()."""
        from sagellm_backend.providers.pytorch_cuda import PyTorchCUDABackendProvider

        backend = PyTorchCUDABackendProvider(device_id=0)
        cap = backend.get_capability()

        assert cap.device_type == "cuda"
        assert cap.total_memory_gb > 0

    def test_create_stream(self):
        """Test create_stream()."""
        from sagellm_backend.providers.pytorch_cuda import PyTorchCUDABackendProvider

        backend = PyTorchCUDABackendProvider(device_id=0)
        stream = backend.create_stream()

        assert stream is not None
        stream.synchronize()

    def test_kv_block_alloc(self):
        """Test KV block allocation."""
        from sagellm_backend.providers.pytorch_cuda import PyTorchCUDABackendProvider

        backend = PyTorchCUDABackendProvider(device_id=0)
        block = backend.kv_block_alloc(1024 * 1024)  # 1 MB

        assert block is not None
        assert block.size_bytes == 1024 * 1024

        backend.kv_block_free(block)


@pytest.mark.npu
@pytest.mark.skipif(True, reason="Requires Ascend NPU - run with --run-npu flag")
class TestPyTorchAscendBackendIntegration:
    """Integration tests for PyTorchAscendBackendProvider (requires NPU)."""

    def test_create_backend(self):
        """Test creating backend provider."""
        from sagellm_backend.providers.pytorch_ascend import (
            PyTorchAscendBackendProvider,
        )

        backend = PyTorchAscendBackendProvider(device_id=0)
        assert backend is not None

    def test_get_capability(self):
        """Test get_capability()."""
        from sagellm_backend.providers.pytorch_ascend import (
            PyTorchAscendBackendProvider,
        )

        backend = PyTorchAscendBackendProvider(device_id=0)
        cap = backend.get_capability()

        assert cap.device_type == "npu"
        assert cap.total_memory_gb > 0
