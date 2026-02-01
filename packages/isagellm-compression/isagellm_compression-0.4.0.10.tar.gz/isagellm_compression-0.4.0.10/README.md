# sagellm-compression

## Protocol Compliance (Mandatory)

- MUST follow Protocol v0.1: https://github.com/intellistream/sagellm-docs/blob/main/docs/specs/protocol_v0.1.md
- Any globally shared definitions (fields, error codes, metrics, IDs, schemas) MUST be added to Protocol first.

[![CI](https://github.com/intellistream/sagellm-compression/actions/workflows/ci.yml/badge.svg)](https://github.com/intellistream/sagellm-compression/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/isagellm-compression.svg)](https://badge.fury.io/py/isagellm-compression)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/gh/intellistream/sagellm-compression/branch/main/graph/badge.svg)](https://codecov.io/gh/intellistream/sagellm-compression)

Inference acceleration tools for LLM: quantization, sparsity, speculative decoding, kernel fusion, and more.

## Features

- Quantization (INT8/INT4)
- Sparsity (structured and unstructured pruning)
- Speculative decoding
- Kernel fusion
- Chain-of-Thought acceleration

## Installation

```bash
pip install isagellm-compression
```

## Quick Start

```python
from sagellm_compression import QuantizationConfig, apply_quantization

config = QuantizationConfig(method="int8", per_channel=True)
quantized_model = apply_quantization(model, config)
```

## Development

```bash
git clone git@github.com:intellistream/sagellm-compression.git
cd sagellm-compression
./quickstart.sh

pip install -e ".[dev]"
pytest tests/ -v
```

## Documentation

- [docs/](docs/)

## 🔄 贡献指南

请遵循以下工作流程：

1. **创建 Issue** - 描述问题/需求
   ```bash
   gh issue create --title "[Bug] 描述" --label "bug,sagellm-compression"
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
