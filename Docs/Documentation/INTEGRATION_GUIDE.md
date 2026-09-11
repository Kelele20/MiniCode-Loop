# MiniCode Loop 集成指南

## 模型供应商

MiniCode 通过 `model_registry.py` 选择适配器，通过 `anthropic_adapter.py` 或 `openai_adapter.py` 形成供应商请求。可使用环境变量或 `~/.mini-code/settings.json` 配置 Anthropic、OpenAI、OpenRouter 和 OpenAI 兼容端点。

示例：

```powershell
$env:OPENAI_API_KEY="..."
$env:ANTHROPIC_MODEL="gpt-4o"
python -m minicode.main --readiness-json
```

Readiness 只检查配置与本地能力。`minicode-provider-smoke` 才可能调用真实供应商，并且必须同时设置 `MINICODE_LIVE_PROVIDER_SMOKE=1` 和 `--run-live`。测试与发布证据生成会把状态放在项目 `.temp`，隔离用户配置并清除供应商凭据，不会自行调用真实模型 API；若离线评估没有生成诊断，发布脚本只记录离线失败证据，不会用 Headless 补发请求。

模型基础 URL 属于受信任的运行配置边界；模型可调用的通用 HTTP 工具另受下述公网策略约束。

## MCP

MCP 使用 stdio 子进程连接，支持工具、资源和 prompt。用户级配置位于 `~/.mini-code/mcp.json`；项目级 `.mcp.json` 默认不受信任，需显式传入：

```powershell
minicode-py --trust-project-mcp
```

MCP 返回内容属于外部输入，不应被当作更高优先级系统指令。MCP 工具仍经过工具注册、输入验证和现有权限边界；容器内只能启动镜像中实际存在的 MCP 命令。

## HTTP 工具边界

`web_fetch` 和 `http_request` 统一调用 `validate_public_http_url`：

1. 解析并规范化 HTTP/HTTPS URL，拒绝凭据和缺失主机。
2. 解析 DNS；全部结果必须满足 `ipaddress.is_global`。
3. 构建带 `SafeRedirectHandler` 的 opener，每次重定向重复步骤 1–2，最多 5 次。
4. 以有限超时执行，并通过 `read_bounded` 截断响应。

因此集成端不得依赖这些工具访问 `localhost`、RFC1918 私网、链路本地、容器内部服务、云元数据 IP、保留或多播地址。若需要本地模型端点，应通过模型供应商配置接入，而不是绕过 HTTP 工具策略。

`http_request` 的 GET/HEAD 是安全校验后的读取；POST/PUT/PATCH/DELETE/OPTIONS 调用 `PermissionManager.ensure_network_request`，每次都必须获得一次性授权。Headless 或其他无 prompt 环境默认拒绝。

## 嵌入 Python

主要内部边界：

```python
from minicode.model_registry import create_model_adapter
from minicode.permissions import PermissionManager
from minicode.tools import create_default_tool_registry

permissions = PermissionManager(workspace_root=".")
tools = create_default_tool_registry()
```

工具执行应传入包含 `cwd` 与 `permissions` 的 `ToolContext`。不要直接调用工具的底层网络函数，否则会绕过注册器的输入校验。

## 容器集成

Docker 构建上下文必须是仓库根，因为 wheel 同时包含 `minicode/`、`Main/` 和 `Package/`：

```powershell
docker build -t minicode-py .
docker compose run --rm cli
docker compose run --rm headless "执行一次任务"
```

工作区挂载到 `/workspace`，用户状态存储在命名卷 `minicode-loop-home`。Compose 当前且仅支持 `cli` 和 `headless`；Gateway/Cron 已退休，不应由部署系统引用。

## 可观测性和失败语义

顶层代理、Headless 和工具安全网会把异常转换为明确失败并记录上下文；可恢复的可选子系统故障使用带堆栈的 debug/warning 日志，不再静默吞掉。使用 `--log-level DEBUG` 或 `MINI_CODE_LOG_LEVEL=DEBUG` 查看详细诊断，使用 `--structured-logs` 输出 JSON 日志。

公开运行与诊断入口是 `minicode-py`、`minicode-headless`、`minicode-readiness`、`minicode-structure-check` 和 `minicode-provider-smoke`。
