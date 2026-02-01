# sagellm-backend

## Protocol Compliance (Mandatory)

- MUST follow Protocol v0.1: <https://github.com/intellistream/sagellm-docs/blob/main/docs/specs/protocol_v0.1.md>
- Any globally shared definitions (fields, error codes, metrics, IDs, schemas) MUST be added to Protocol first.

[![CI](https://github.com/intellistream/sagellm-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/intellistream/sagellm-backend/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/isagellm-backend.svg)](https://badge.fury.io/py/isagellm-backend)
[![Python Version](https://img.shields.io/pypi/pyversions/isagellm-backend.svg)](https://pypi.org/project/isagellm-backend/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

硬件抽象层 - 为 sageLLM 提供统一的硬件接口（CUDA/Ascend/Kunlun）

## 架构定位

```text
┌─────────────────────────────────────────────────────────────┐
│  sagellm-core (引擎协调层)                                   │
│  • LLMEngine (硬件无关的统一引擎)                           │
│  • 自动选择最佳后端 (cuda > ascend > cpu)                  │
├─────────────────────────────────────────────────────────────┤
│  sagellm-backend (硬件抽象层) ← 本仓库                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  BackendProvider Interface                         │    │
│  │  • Stream/Event 异步流                              │    │
│  │  • KVBlock 内存管理                                 │    │
│  │  • Collective 操作（all_reduce/all_gather）        │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  CUDA    │  │  Ascend  │  │  Kunlun  │                  │
│  │ Provider │  │ Provider │  │ Provider │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
├─────────────────────────────────────────────────────────────┤
│  Hardware SDK Layer                                          │
│  CUDA/cuDNN/NCCL │ CANN/HCCL │ XPU SDK │ DCU SDK           │
└─────────────────────────────────────────────────────────────┘
```

**职责分离（v0.2.0 重构）**：

- ✅ **本仓库负责**：硬件抽象、设备管理、内存原语
- ❌ **不再包含**：BaseEngine, EngineFactory（已移至 sagellm-core）
- 🔗 **被使用于**：sagellm-core 中的引擎实现

## Features

- **统一硬件抽象**：单一 API 支持多硬件后端
- **CPU Backend**：无 GPU 环境的默认后端
- **CUDA Support**：原生 CUDA 后端实现
- **CPU Support**：CPU-only 后端实现
- **能力发现**：硬件能力查询与验证

## Installation

```bash
pip install isagellm-backend
```

## Quick Start

```bash
git clone git@github.com:intellistream/sagellm-backend.git
cd sagellm-backend
./quickstart.sh

# Run tests
pytest tests/ -v
```

## Usage Examples

### Basic Backend Usage

```python
from sagellm_backend import CPUBackendProvider, DType

# Create backend
backend = CPUBackendProvider()

# Query capabilities
cap = backend.capability()
print(cap.supported_dtypes)

# Allocate KV block
block = backend.kv_block_alloc(128, DType.FP16)
```

### Using with sagellm-core LLMEngine

Backend 现在专注于硬件抽象，引擎使用 `sagellm-core` 的 `LLMEngine`。

```python
# LLMEngine 位于 sagellm-core
from sagellm_core import LLMEngine, LLMEngineConfig

# LLMEngine 自动选择最佳后端
config = LLMEngineConfig(
    model_path="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    backend_type="auto",  # 自动选择: cuda > ascend > cpu
    max_new_tokens=100,
)
engine = LLMEngine(config)
await engine.start()

# 推理
output = await engine.generate("Hello, world!")
print(output)

await engine.stop()
```

## Extending with New Backends

```python
# Create provider in providers/ directory
class AscendBackendProvider:
    def capability(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            supported_dtypes=[DType.FP16, DType.BF16, DType.INT8],
            # ...
        )

    # Implement other interface methods...

# Register via entry point in pyproject.toml
[project.entry-points."sagellm.backends"]
ascend_cann = "sagellm_backend.providers.ascend:create_ascend_backend"
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Contributing](CONTRIBUTING.md)
- [Team](docs/TEAM.md)

## 🔄 贡献指南

请遵循以下工作流程：

1. **创建 Issue** - 描述问题/需求

   ```bash
   gh issue create --title "[Bug] 描述" --label "bug,sagellm-backend"
   ```

2. **开发修复** - 在本地 `fix/#123-xxx` 分支解决

   ```bash
   git checkout -b fix/#123-xxx origin/main-dev
   # 开发、测试...
   pytest -v
   ruff format . && ruff check . --fix
   ```

3. **发起 PR** - 提交到 `main-dev` 分支

   ```bash
   gh pr create --base main-dev --title "Fix: 描述" --body "Closes #123"
   ```

4. **合并** - 审批后合并到 `main-dev`

更多详情见 [.github/copilot-instructions.md](.github/copilot-instructions.md)

## License

Proprietary
