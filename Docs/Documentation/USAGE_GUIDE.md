# MiniCode Loop 使用指南

## CLI

安装开发环境后运行：

```powershell
minicode-py
# 等价入口
python -m minicode.main
```

### 配置文件与密钥

本地 Python 进程不会自动读取项目目录中的 `.env`；`.env.example` 只是变量模板。持久配置应写入用户级 `~/.mini-code/settings.json`，也可以在当前终端设置环境变量：

```json
{
  "model": "claude-sonnet-4-20250514",
  "env": {
    "ANTHROPIC_API_KEY": "..."
  }
}
```

`python -m minicode.main --install` 可按提示写入用户配置。用户配置位于仓库之外，不要复制到项目目录或提交到 Git；真实密钥只用于需要供应商调用的运行路径。

常用启动选项：

```powershell
minicode-py --resume latest
minicode-py --list-workspace-sessions
minicode-py --inspect-session latest
minicode-py --replay-session latest
minicode-py --preview-rewind latest
minicode-py --list-checkpoints latest
minicode-py --readiness-json
minicode-py --validate-config
```

项目级 `.mcp.json` 默认不加载。只对可信仓库使用 `--trust-project-mcp` 或 `MINI_CODE_TRUST_PROJECT_MCP=1`。

## Headless

```powershell
minicode-headless "只读分析项目结构"
"总结当前目录" | python -m minicode.headless
```

无交互输入时，写文件、命令、越界路径和网络写请求默认拒绝。`--allow-edits` 仅适用于你明确控制的环境：

```powershell
minicode-headless --allow-edits "修改指定文件并运行测试"
```

## 网络工具

`web_fetch` 用于读取网页；`http_request` 支持 `GET`、`HEAD`、`POST`、`PUT`、`PATCH`、`DELETE` 和 `OPTIONS`。两者仅允许公共 HTTP/HTTPS 目标。

安全规则：

- 禁止 `file:`、`ftp:` 等协议和 URL 内嵌凭据。
- 禁止 localhost、回环、私网、链路本地、保留、多播、云元数据及非规范数字地址。
- DNS 返回多个地址时，每个地址都必须是公网；重定向每一跳重新检查，最多 5 跳。
- `http_request.timeout` 必须在 1–60 秒；请求体不超过 100,000 字节。
- `web_fetch` 最多读取 200,000 字节且最多返回 50,000 字符；`http_request` 最多读取 50,000 字节。

授权规则：

- `GET`、`HEAD`：通过 URL 安全校验后可读。
- 其他方法：调用 `PermissionManager.ensure_network_request(method, url)`，只提供“允许一次”或“拒绝一次”。
- 非交互环境没有审批器时返回 `Network request requires approval`，不会偷偷发送请求。

典型错误：

```text
non-public network address is blocked: 127.0.0.1
credentials embedded in URLs are not allowed
url scheme must be http or https
Network request denied: POST https://example.com/api
```

## Docker

```powershell
docker build -t minicode-py .
docker compose run --rm cli
docker compose run --rm headless "分析当前工作区"
```

`cli` 开启 stdin 和 TTY，直接进入交互界面；`headless` 使用 `python -m minicode.headless`。镜像内包含 `minicode/`、`Main/` 和 `Package/`。Compose 只有这两个服务；Gateway/Cron 已退休。

## 就绪诊断

```powershell
minicode-readiness --json
minicode-readiness --doctor
minicode-readiness --repair-plan
minicode-readiness --patch-preview
```

这些命令只读本地配置，不调用真实供应商。真实冒烟要求双重显式授权：

```powershell
$env:MINICODE_LIVE_PROVIDER_SMOKE="1"
minicode-provider-smoke --run-live --timeout 45
```

## 测试和开发

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m mypy minicode Main Package
python -m ruff check minicode Main Package tests
python -m minicode.structure_check --root . --check-material-inventory
python -m build
```

pytest 会自动发现 `tests/test_*.py` 和 `Main/Package` 的 `*.Test.py`；无需单独传测试目录。

`python benchmarks/release_readiness.py` 会生成离线发布证据：子进程使用隔离用户目录且不继承供应商凭据。只有前述 `minicode-provider-smoke --run-live` 双重授权路径允许真实请求。

## 当前入口

当前公开命令只有 `minicode-py`、`minicode-headless`、`minicode-readiness`、`minicode-structure-check`、`minicode-provider-smoke`。目录和组件说明见 [STRUCTURE.md](STRUCTURE.md)，供应商与 MCP 边界见 [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)。
