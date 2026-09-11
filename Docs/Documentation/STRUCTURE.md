# MiniCode Loop 当前结构

本文只描述当前仓库。产品根使用 Product Project Root profile；`.git/`、`.temp/`、`CLAUDE.md` 是固定过程载体，不进入产品结构投影。本仓库当前没有 `.git/`。

## 根目录

```text
MiniCode-Loop/
├─ minicode/                         Python 运行包
├─ Main/MinicodeFrontline/          Main 模块：公开产品表面投影
├─ Package/EngineeringStructure/    Package 模块：结构规则与扫描实现
├─ tests/                            根级核心回归测试
├─ benchmarks/                       隔离供应商配置的可复现评估和发布证据
├─ outputs/                          规范化评估输出
├─ Docs/Documentation/              当前文档与历史记录
├─ pyproject.toml
├─ Dockerfile
├─ docker-compose.yml
└─ .env.example
```

缓存、字节码和本地状态不是产品模块。它们可删除，或位于扫描器认可的过程载体中。

## 公开入口

| 命令 | Python 入口 | 职责 |
| --- | --- | --- |
| `minicode-py` | `minicode.main:main` | 交互式 CLI/TUI、会话、管理命令 |
| `minicode-headless` | `minicode.headless:main` | 非交互单轮执行 |
| `minicode-readiness` | `minicode.readiness:main` | 本地供应商与 fallback 就绪诊断 |
| `minicode-structure-check` | `minicode.structure_check:main` | 结构、材料和文档一致性门禁 |
| `minicode-provider-smoke` | `minicode.provider_smoke:main` | 双重显式授权的真实供应商请求 |

## 运行包职责

- `main.py`、`tty_app.py`、`tui/`：交互入口、输入事件、渲染与审批界面。
- `headless.py`：无 TTY 的单轮生命周期；默认拒绝需要交互审批的操作。
- `agent_loop.py`、`turn_kernel.py`、`turn_events.py`：代理循环、步骤状态、统一事件和工具调度。
- `model_registry.py`、`anthropic_adapter.py`、`openai_adapter.py`：模型选择与供应商协议适配。
- `tooling.py`、`tools/`：工具注册、验证和执行。
- `network_safety.py`：公共 HTTP(S) URL 验证、DNS 地址判定、重定向复验、超时与响应上限。
- `permissions.py`：路径、命令、编辑和网络写请求授权；`ensure_network_request(method, url)` 是网络授权入口。
- `session.py`、`session_contract.py`、`memory.py`、`memory_pipeline.py`：会话、兼容持久化、记忆检索与维护。
- `context_manager.py`、`context_compactor.py`、`context_cybernetics.py`：上下文计量、压缩和保护。
- `mcp.py`、`skills.py`、`hooks.py`：MCP、技能和钩子扩展边界。
- `readiness.py`、`release_readiness.py`、`provider_smoke.py`：就绪报告、发布证据和显式在线冒烟。

Gateway 与 Cron 已退休；不存在对应 Python 模块、console script 或 Compose 服务。

## 网络调用链

```text
web_fetch / http_request
        -> validate_public_http_url
        -> PermissionManager.ensure_network_request（非 GET/HEAD）
        -> SafeRedirectHandler（每跳复验，最多 5 跳）
        -> bounded response reader
```

URL 校验仅允许 HTTP/HTTPS，拒绝内嵌凭据和任何非全局地址。请求体、响应体和超时边界见 [使用指南](USAGE_GUIDE.md)。

## 测试布局

`pyproject.toml` 的 pytest 配置同时扫描：

- `tests/test_*.py`：网络安全和交付表面核心回归。
- `Main/**/Test/**/*.Test.py`：Main 源码的精确镜像测试。
- `Package/**/Test/**/*.Test.py`：Package 源码的精确镜像测试。

统一使用 `--import-mode=importlib`。Windows 链接载体测试使用真实 directory junction/reparse point，Unix 使用真实符号链接；不得以 skip 或 mock 代替载体行为。

## 结构与材料门

`Package/EngineeringStructure/Src/Application/Query/ProductRootProjection.py` 负责载体和结构投影，`StructureCompliance.py` 负责 Python 依赖方向。`minicode.structure_check` 组合两者，并在 `--check-material-inventory` 下检查：

- 清单登记路径与命令目标存在；
- 五个公开入口同时出现在 README 和对应专题文档；
- 当前文档不宣称已退休服务可用；
- `README.md` 必须存在，`README.zh-CN.md` 可选；
- 清单声明的发布证据命令在 README 中可找到。

权威材料清单位于 `Docs/Documentation/engineering/material-inventory.json`。
