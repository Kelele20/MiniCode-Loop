# MiniCode Loop 代码百科

本文是当前实现索引，不记录已删除源码的历史细节。带日期的 `superpowers/specs`、`superpowers/plans` 和报告属于历史资料，不代表当前实现。

## 产品表面

MiniCode Loop 是 Python 3.11+ 的终端编码代理。公开入口只有：

- `minicode-py`：交互式 CLI/TUI。
- `minicode-headless`：非交互单轮运行。
- `minicode-readiness`：只读就绪诊断。
- `minicode-structure-check`：结构、材料和文档门禁。
- `minicode-provider-smoke`：显式在线供应商冒烟。

Gateway 和 Cron 已退休；没有可调用模块、命令、环境变量或容器服务。

## 主调用链

```text
main / headless
  -> config + PermissionManager
  -> model_registry -> Anthropic/OpenAI adapter
  -> run_agent_turn
       -> prompt/context/memory
       -> ToolRegistry
            -> filesystem / command / MCP / network tools
       -> session + transcript + metrics
```

`turn_kernel.py` 保存每轮的递归状态，`turn_events.py` 将 assistant、progress、tool 和 runtime 事件统一交给 TUI 或其他消费者。旧式回调仍作为兼容入口，但不会改变模型协议选择。

`release_readiness.py` 校验发布证据和报告格式。证据生成器把共享会话状态和 pytest 临时目录放在项目 `.temp`，隔离用户配置并清除供应商凭据；离线评估缺少供应商诊断时只记录失败证据，不会启动 Headless 补发请求。运行时评估的控制器状态同样只写入项目 `.temp`。

## 安全边界

文件、命令和工作区外路径由 `permissions.py` 审批。网络工具通过 `network_safety.py` 强制公共 HTTP/HTTPS：解析的全部 IP 必须为全局地址，重定向逐跳复验，并限制跳数、超时、请求体及响应体。

`web_fetch` 是只读抓取；`http_request` 的 GET/HEAD 是安全校验后的读取，其余方法经 `ensure_network_request(method, url)` 一次性授权。没有交互审批器时拒绝网络写。

## 状态与连续性

- `session.py` 和 `session_contract.py`：会话保存、索引、恢复、回放和 rewind checkpoint。
- `memory.py` 和 `memory_pipeline.py`：多作用域记忆、检索、注入、反思和维护。
- `context_manager.py`、`context_compactor.py`、`context_cybernetics.py`：token 估算、压缩、熔断和恢复。
- `logging_config.py`：普通或结构化日志；必要的顶层异常安全网记录完整上下文。

## 工具与扩展

`tooling.py` 定义 `ToolDefinition`、`ToolResult`、`ToolContext` 和注册器。`tools/` 包含文件、搜索、编辑、命令、归档、数据、代码导航、测试、网络与 task 工具。`mcp.py` 连接显式配置的 stdio MCP 服务；`skills.py` 和 `hooks.py` 提供扩展点。

## 工程模块

`Main/MinicodeFrontline` 是产品入口投影，公开运行生命周期、命令表面和运行能力清单。`Package/EngineeringStructure` 是可复用的结构扫描 Package，包含产品根投影和 Python 依赖边界检查。两者的 `Test/` 与 `Src/` 精确镜像。

根 `tests/` 保存网络攻击向量、网络权限、Docker/Compose、console script 和交付回归。pytest 从根测试和两个工程模块自动发现测试。

## 质量门

```powershell
python -m pytest -q
python -m mypy minicode Main Package
python -m ruff check minicode Main Package tests
python -m minicode.structure_check --root . --check-material-inventory
python -m build
```

详细目录见 [STRUCTURE.md](STRUCTURE.md)，使用方法见 [USAGE_GUIDE.md](USAGE_GUIDE.md)，外部集成见 [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)。
