# sagellm-comm

## Protocol Compliance (Mandatory)

- MUST follow Protocol v0.1: https://github.com/intellistream/sagellm-docs/blob/main/docs/specs/protocol_v0.1.md
- Any globally shared definitions (fields, error codes, metrics, IDs, schemas) MUST be added to Protocol first.

[![CI](https://github.com/intellistream/sagellm-comm/actions/workflows/ci.yml/badge.svg)](https://github.com/intellistream/sagellm-comm/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/isagellm-comm.svg)](https://badge.fury.io/py/isagellm-comm)
[![Python Version](https://img.shields.io/pypi/pyversions/isagellm-comm.svg)](https://pypi.org/project/isagellm-comm/)
[![codecov](https://codecov.io/gh/intellistream/sagellm-comm/branch/main/graph/badge.svg)](https://codecov.io/gh/intellistream/sagellm-comm)

**Network Communication Layer** for sageLLM distributed inference engine.

## Overview

This package provides efficient communication primitives for distributed LLM inference:

| 功能 | 任务 | 说明 |
|------|------|------|
| **拓扑发现** | Task1.1 | 自动发现节点、GPU、互联拓扑 |
| **集合操作** | Task1.2 | AllReduce, AllGather, ReduceScatter 等 |
| **计算/通信重叠** | Task1.4, 1.8 | Multi-stream overlap, pipeline |
| **国产互联适配** | Task1.5, 1.6 | CXL/UB/RDMA 适配器 |
| **跨节点通信** | Task1.7 | 跨节点集合操作优化 |

> **注意**: Task1.3 (KV Transfer) 已移至 `sagellm-kv-cache` 仓库，本包提供底层 `CommBackend` 供其使用。

### 📦 职责边界

```
┌─────────────────────────────────────────────────────────────────────┐
│                         sagellm-core                                 │
│                    (分布式推理：TP/PP 并行)                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │ 使用 CommBackend 进行张量通信
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       sagellm-comm (本仓库)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Topology   │  │ Collective  │  │   Overlap   │  │  Domestic   │ │
│  │  (Task1.1)  │  │  (Task1.2)  │  │ (Task1.4/8) │  │  (Task1.5)  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│                      CommBackend Interface                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   NCCL   │  │   HCCL   │  │   RCCL   │  │   Gloo   │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────────────────┘
                             ▲
                             │ KV Transfer 使用 CommBackend
┌────────────────────────────┴────────────────────────────────────────┐
│                      sagellm-kv-cache                                │
│                   (KV Transfer 使用本包的网络能力)                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 🔍 Research Context

**sagellm-comm** is conceptually similar to the **Transfer Engine** in [Mooncake](https://github.com/kvcache-ai/Mooncake):

| Aspect | Mooncake Transfer Engine | sagellm-comm |
|--------|-------------------------|--------------|
| **Core Function** | KV cache data movement | Network communication layer |
| **Scope** | Cross-node KV transfer | Topology + collectives + overlap |
| **Focus** | RDMA/NVLink optimization | Hardware-agnostic abstraction |
| **KV Transfer** | Integrated | Provided to sagellm-kv-cache |

**Key differences**:
- **sagellm-comm** provides a **unified communication layer** that integrates with sageLLM's backend abstraction, supporting NCCL, HCCL, and domestic interconnects (CXL/UB/RDMA)
- **Compute/communication overlap** (Task1.4/1.8) is a first-class design goal
- **Adapter pattern** ensures zero vendor lock-in: swappable backends without core logic changes
- **KV Transfer (Task1.3)** is implemented in sagellm-kv-cache, using this package's `CommBackend` for data-aware optimization

## Installation

```bash
# 从 PyPI 安装（自动安装依赖）
pip install isagellm-comm
```

## 🚀 开发者快速开始

```bash
git clone git@github.com:intellistream/sagellm-comm.git
cd sagellm-comm
./quickstart.sh   # 一键安装开发环境（含依赖）

# 或手动安装
pip install -e ".[dev]"
```

运行测试：
```bash
pytest tests/ -v
```

> 💡 `isagellm-protocol` 和 `isagellm-backend` 会自动从 PyPI 安装。

## Quick Start

```python
from sagellm_comm import CommGroup, Topology, CollectiveOps

# Discover topology
topology = Topology.discover()

# Create communication group
group = CommGroup.create(world_size=4, rank=0)

# Collective operations (for distributed inference)
CollectiveOps.all_reduce(tensor, group=group)
CollectiveOps.all_gather(tensor, group=group)
```

> **Note**: For KV block transfer, use `sagellm-kv-cache.KVTransferEngine` which utilizes this package's `CommBackend` internally.

## Supported Backends

- NCCL (NVIDIA)
- HCCL (Huawei Ascend)
- RCCL (AMD ROCm)
- Gloo (CPU fallback)

## Dependencies

- `isagellm-protocol>=0.1.0` - Protocol definitions
- `isagellm-backend>=0.1.0` - Backend abstraction

## Development

### Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to ensure code quality:

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files (automatic on git commit)
git commit

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

Configured hooks:
- Ruff linter and formatter
- MyPy type checking
- Trailing whitespace, end-of-file fixer
- YAML/TOML/JSON validation

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=sagellm_comm --cov-report=html

# Run specific test file
pytest tests/test_imports.py -v
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check . --fix

# Type check
mypy src/
```

## 🔄 贡献指南

请遵循以下工作流程：

1. **创建 Issue** - 描述问题/需求
   ```bash
   gh issue create --title "[Bug] 描述" --label "bug,sagellm-comm"
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

Private - IntelliStream Research Project
