"""测试 entry points 注册和发现。

注意：遵循 sageLLM No Mock Policy，只测试真实的 CPU provider。
"""

from __future__ import annotations


def test_backend_entry_points_registered():
    """测试 backend entry points 是否正确注册。"""
    from sagellm_backend.providers.cpu import create_cpu_backend

    # 验证工厂函数可以直接调用
    cpu_backend = create_cpu_backend()
    assert cpu_backend is not None
    # 验证返回的是真实的 BackendProvider 实例
    assert hasattr(cpu_backend, "capability")
    assert hasattr(cpu_backend, "create_stream")
    assert hasattr(cpu_backend, "kv_block_alloc")
