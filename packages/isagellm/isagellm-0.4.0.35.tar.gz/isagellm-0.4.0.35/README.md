# sageLLM

## Protocol Compliance (Mandatory)

- MUST follow Protocol v0.1:
  https://github.com/intellistream/sagellm-docs/blob/main/docs/specs/protocol_v0.1.md
- Any globally shared definitions (fields, error codes, metrics, IDs, schemas) MUST be added to
  Protocol first.

<p align="center">
  <strong>🚀 Modular LLM Inference Engine for Domestic Computing Power</strong>
</p>

<p align="center">
  Ollama-like experience for Chinese hardware ecosystems (Huawei Ascend, NVIDIA)
</p>

______________________________________________________________________

## ✨ Features

- 🎯 **One-Click Install** - `pip install isagellm` gets you started immediately
- 🧠 **CPU-First** - Default CPU engine, no GPU required
- 🇨🇳 **Domestic Hardware** - First-class support for Huawei Ascend NPU
- 📊 **Observable** - Built-in metrics (TTFT, TBT, throughput, KV usage)
- 🧩 **Plugin System** - Extend with custom backends and engines

## 📦 Quick Install

```bash
# Install sageLLM (CPU-first, no GPU required)
pip install isagellm

# With Control Plane (request routing & scheduling)
pip install 'isagellm[control-plane]'

# With API Gateway (OpenAI-compatible REST API)
pip install 'isagellm[gateway]'

# Full server (Control Plane + Gateway)
pip install 'isagellm[server]'

# With CUDA support
pip install 'isagellm[cuda]'

# All features
pip install 'isagellm[all]'
```

### 🚀 国内加速安装 PyTorch（推荐）

由于 PyTorch CUDA 版本从官方源下载较慢（~800MB），我们在 GitHub Releases 提供预先下载的 wheels：

```bash
# 方法 1：使用 sagellm CLI (推荐，最简单)
pip install isagellm
sage-llm install cuda --github     # 从 GitHub 下载，快速
sage-llm install cuda              # 从官方源下载（默认）

# 方法 2：直接使用 pip --find-links
pip install torch==2.5.1+cu121 torchvision torchaudio \
  --find-links https://github.com/intellistream/sagellm-pytorch-wheels/releases/download/v2.5.1-cu121/ \
  --trusted-host github.com
```

**其他支持的后端**：

- `sage-llm install ascend` - 华为昇腾 NPU
- `sage-llm install kunlun` - 百度昆仑 XPU
- `sage-llm install haiguang` - 海光 DCU
- `sage-llm install cpu` - CPU-only（最小下载）

💡 **为什么使用 GitHub 加速？**

- ✅ 国内访问速度快（GitHub CDN）
- ✅ 无需配置镜像源
- ✅ 官方 wheels，100% 可信

📦 **Wheels 仓库**: https://github.com/intellistream/sagellm-pytorch-wheels

## 🚀 Quick Start

### CLI (像 vLLM/Ollama 一样简单)

```bash
# 一键启动（完整栈：Gateway + Engine）
pip install 'isagellm[gateway]'
sage-llm serve --model Qwen2-7B

# ✅ OpenAI API 自动可用
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen2-7B",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# 查看系统信息
sage-llm info

# 单次推理（不启动服务器）
sage-llm run -p "What is LLM inference?"

# 高级用法：分布式部署（分别启动各组件）
sage-llm serve --engine-only --port 9000   # 仅引擎
sage-llm gateway --port 8000                # 仅 Gateway
```

### Python API (Control Plane - Recommended)

```python
import asyncio

from sagellm import ControlPlaneManager, BackendConfig, EngineConfig

# Install with: pip install 'isagellm[control-plane]'
async def main() -> None:
    manager = ControlPlaneManager(
        backend_config=BackendConfig(kind="cpu", device="cpu"),
        engine_configs=[
            EngineConfig(
                kind="cpu",
                model="sshleifer/tiny-gpt2",
                model_path="sshleifer/tiny-gpt2"
            )
        ]
    )

    await manager.start()
    try:
        # Requests are automatically routed to available engines
        response = await manager.execute_request(
            prompt="Hello, world!",
            max_tokens=128
        )
        print(response.output_text)
        print(f"TTFT: {response.metrics.ttft_ms:.2f} ms")
        print(f"Throughput: {response.metrics.throughput_tps:.2f} tokens/s")
    finally:
        await manager.stop()


asyncio.run(main())
```

**⚠️ Important:** Direct engine creation (`create_engine()`) is not exported from the umbrella
package. All production code must use `ControlPlaneManager` for proper request routing, scheduling,
and lifecycle management.

### Configuration

```yaml
# ~/.sage-llm/config.yaml
backend:
  kind: cpu  # Options: cpu, pytorch-cuda, pytorch-ascend
  device: cpu

engine:
  kind: cpu
  model: sshleifer/tiny-gpt2

control_plane:
  endpoint: "localhost:8080"
```

## 📊 Metrics & Validation

sageLLM provides comprehensive performance metrics:

```json
{
  "ttft_ms": 45.2,
  "tbt_ms": 12.5,
  "throughput_tps": 80.0,
  "peak_mem_mb": 24576,
  "kv_used_tokens": 4096,
  "prefix_hit_rate": 0.85
}
```

Run benchmarks:

```bash
sage-llm demo --workload year1 --output metrics.json
```

## 🏗️ Architecture

```
isagellm (umbrella package)
├── isagellm-protocol       # Protocol v0.1 types
│   └── Request, Response, Metrics, Error, StreamEvent
├── isagellm-backend        # Hardware abstraction (L1 - Foundation)
│   └── BackendProvider, CPUBackend, (CUDABackend, AscendBackend)
├── isagellm-comm           # Communication primitives (L2 - Infrastructure)
│   └── Topology, CollectiveOps (all_reduce/gather), P2P (send/recv), Overlap
├── isagellm-kv-cache       # KV cache management (L2 - Optional)
│   └── PrefixCache, MemoryPool, EvictionPolicies, Predictor, KV Transfer
├── isagellm-compression    # Inference acceleration (quantization, sparsity, etc.) (L2 - Optional)
│   └── Quantization, Sparsity, SpeculativeDecoding, Fusion
├── isagellm-core           # Engine core & runtime (L3)
│   └── Config, Engine, Factory, DemoRunner, Adapters (vLLM/LMDeploy)
├── isagellm-control-plane  # Request routing & scheduling (L4 - Optional)
│   └── ControlPlaneManager, Router, Policies, Lifecycle
└── isagellm-gateway        # OpenAI-compatible REST API (L5 - Optional)
    └── FastAPI server, /v1/chat/completions, Session management
```

## 🔧 Development

### Quick Setup (Development Mode)

```bash
# Clone all repositories
./scripts/clone-all-repos.sh

# Install all packages in editable mode
./quickstart.sh

# Open all repos in VS Code Multi-root Workspace
code sagellm.code-workspace
```

**📖 See [WORKSPACE_GUIDE.md](WORKSPACE_GUIDE.md) for Multi-root Workspace usage.**

### Testing

```bash
# Clone and setup
git clone https://github.com/IntelliStream/sagellm.git
cd sagellm
pip install -e ".[dev]"

# Run tests
pytest -v

# Format & lint
ruff format .
ruff check . --fix

# Type check
mypy src/sagellm/

# Verify dependency hierarchy
python scripts/verify_dependencies.py
```

### 📖 Development Resources

- **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - 完整部署与配置指南
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - 故障排查快速参考
- **[ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md)** - 环境变量完整参考
- **[DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)** - 开发者指南
- **[WORKSPACE_GUIDE.md](docs/WORKSPACE_GUIDE.md)** - Multi-root Workspace 使用
- **[INFERENCE_FLOW.md](docs/INFERENCE_FLOW.md)** - 推理流程详解
- **[PR_CHECKLIST.md](docs/PR_CHECKLIST.md)** - Pull Request 检查清单

______________________________________________________________________

## 📚 Documentation Index

### 用户文档

- [快速开始](README.md#-quick-start) - 5 分钟上手
- [部署指南](docs/DEPLOYMENT_GUIDE.md) - 生产环境部署
- [配置参考](docs/DEPLOYMENT_GUIDE.md#%E9%85%8D%E7%BD%AE%E6%96%87%E4%BB%B6%E8%AF%B4%E6%98%8E) - 完整配置选项
- [环境变量](docs/ENVIRONMENT_VARIABLES.md) - 环境变量参考
- [故障排查](docs/TROUBLESHOOTING.md) - 常见问题解决

### 开发者文档

- [开发指南](docs/DEVELOPER_GUIDE.md) - 贡献代码
- [架构设计](README.md#-architecture) - 系统架构
- [Workspace 使用](docs/WORKSPACE_GUIDE.md) - Multi-root 工作区
- [PR 检查清单](docs/PR_CHECKLIST.md) - 提交前检查

### API 文档

- OpenAI 兼容 API - 参见 [sagellm-gateway](https://github.com/intellistream/sagellm-gateway)
- Python API - 参见 [API_REFERENCE.md](docs/API_REFERENCE.md)（待补充）

### 子包文档

- [sagellm-protocol](https://github.com/intellistream/sagellm-protocol) - 协议定义

- [sagellm-backend](https://github.com/intellistream/sagellm-backend) - 后端抽象

- [sagellm-core](https://github.com/intellistream/sagellm-core) - 引擎核心

- [sagellm-control-plane](https://github.com/intellistream/sagellm-control-plane) - 控制面

- [sagellm-gateway](https://github.com/intellistream/sagellm-gateway) - API 网关

- [sagellm-benchmark](https://github.com/intellistream/sagellm-benchmark) - 基准测试

- [**DEVELOPER_GUIDE.md**](DEVELOPER_GUIDE.md) - 架构规范与开发指南

- [**PR_CHECKLIST.md**](PR_CHECKLIST.md) - Pull Request 审查清单

- [**scripts/verify_dependencies.py**](scripts/verify_dependencies.py) - 依赖层次验证

## � 贡献指南

### 工作流程（必须遵循）

在提交代码前，**必须**严格遵循以下步骤：

#### 1️⃣ 创建 Issue

描述你要解决的问题、实现的功能或改进：

```bash
gh issue create \
  --title "[Category] 简短描述" \
  --label "bug,sagellm-core" \
  --body "详细描述..."
```

**Issue 类型**：

- `[Bug]` - Bug 修复
- `[Feature]` - 新功能
- `[Performance]` - 性能优化
- `[Integration]` - 与其他模块集成
- `[Docs]` - 文档改进

#### 2️⃣ 在本地分支开发

创建开发分支并解决问题：

```bash
# 从 main-dev 创建分支（不是 main！）
git fetch origin main-dev
git checkout -b fix/#123-short-description origin/main-dev

# 进行开发
# ...

# 确保通过所有检查
ruff format .
ruff check . --fix
pytest -v
```

**分支命名约定**：

- Bug 修复：`bugfix/#123-xxx`
- 新功能：`feature/#456-xxx`
- 文档：`docs/#789-xxx`
- 性能：`perf/#101-xxx`

#### 3️⃣ 发起 Pull Request

提交代码供审查：

```bash
git push origin fix/#123-short-description
gh pr create \
  --base main-dev \
  --head fix/#123-short-description \
  --title "Fix: [简短描述]" \
  --body "解决 #123

## 改动
- 改动 1
- 改动 2

## 测试
- 新增单元测试
- 所有测试通过 ✓"
```

**PR 必须包含**：

- 清晰的标题（Fix/Feature/Docs/Perf）
- 关联 issue 号：`Closes #123`
- 改动列表和测试说明
- 通过所有 CI 检查

#### 4️⃣ 代码审查与合并

等待审批后合并到 `main-dev`：

```bash
# 在 GitHub 界面点击"Merge"按钮
# 合并到 main-dev（不是 main！）
```

**合并前条件**：

- ✅ 至少一名维护者审批
- ✅ CI 检查全部通过（pytest, ruff）
- ✅ 合并到 `main-dev` 分支

### 快速检查清单

在发起 PR 前检查：

- [ ] 从 `main-dev` 分支创建开发分支
- [ ] 更新了 `CHANGELOG.md`
- [ ] `ruff format .` 格式化代码
- [ ] `ruff check . --fix` 通过 lint
- [ ] `pytest -v` 通过所有测试
- [ ] 关联了相关 issue：`Closes #123`

### 反面例子 ❌

- ❌ 直接在 `main` 分支提交
- ❌ PR 中没有关联 issue
- ❌ 修改了代码但没有更新 CHANGELOG
- ❌ 代码没有通过 lint 检查
- ❌ 提交前没有运行测试

### 相关资源

- **Issue Labels**：`bug`, `enhancement`, `documentation`, `sagellm-core`, `sagellm-backend` 等
- **GitHub CLI**：`gh issue create`, `gh pr create`
- **更多信息**：见 `.github/copilot-instructions.md`

## �📚 Package Details

| Package          | PyPI Name           | Import Name        | Description                     |
| ---------------- | ------------------- | ------------------ | ------------------------------- |
| sagellm          | `isagellm`          | `sagellm`          | Umbrella package (install this) |
| sagellm-protocol | `isagellm-protocol` | `sagellm_protocol` | Protocol v0.1 types             |
| sagellm-core     | `isagellm-core`     | `sagellm_core`     | Runtime & config                |
| sagellm-backend  | `isagellm-backend`  | `sagellm_backend`  | Hardware abstraction            |

## 📄 License

Proprietary - IntelliStream. Internal use only.

______________________________________________________________________

<p align="center">
  <sub>Built with ❤️ by IntelliStream Team for domestic AI infrastructure</sub>
</p>
# test
