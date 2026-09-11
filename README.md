# MiniCode Loop

MiniCode Loop（中文名：MiniCode 闭环编程助手）是一个面向本地开发工作流的终端编程助手，支持交互式 CLI 和一次性 Headless 执行。当前支持 Python 3.11+，运行时无第三方依赖；开发质量门依赖 pytest、Hypothesis、mypy、Ruff 和 build。

## 安装

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Linux/macOS 将激活命令替换为 `source .venv/bin/activate`。复制 `.env.example` 仅用于了解变量；本地 Python 进程不会自动读取 `.env`，密钥应通过环境变量或 `python -m minicode.main --install` 写入用户配置。

至少配置一个供应商密钥，例如：

```powershell
$env:ANTHROPIC_API_KEY="..."
$env:ANTHROPIC_MODEL="claude-sonnet-4-20250514"
```

也支持 OpenAI、OpenRouter 和 OpenAI 兼容端点；详见 [集成指南](Docs/Documentation/INTEGRATION_GUIDE.md)。

## 运行

交互式 CLI：

```powershell
minicode-py
# 或
python -m minicode.main
```

Headless：

```powershell
minicode-headless "分析当前项目并给出结论"
"解释当前目录" | python -m minicode.headless
```

Headless 默认拒绝写文件、执行命令、访问工作区外路径以及需要确认的网络写请求。只在可信环境中使用 `--allow-edits`；网络写请求仍由权限层逐次判定。

五个稳定公开命令名称如下：

| 命令 | 用途 |
| --- | --- |
| `minicode-py` | 交互式 CLI/TUI |
| `minicode-headless` | 非交互单轮执行 |
| `minicode-readiness` | 本地模型与运行环境就绪诊断 |
| `minicode-structure-check` | 结构、材料清单与文档一致性检查 |
| `minicode-provider-smoke` | 显式授权的真实供应商冒烟请求 |

```powershell
python -m minicode.main --help
python -m minicode.headless --help
python -m minicode.readiness --help
python -m minicode.structure_check --help
python -m minicode.provider_smoke --help
```

真实供应商调用不会出现在默认测试或发布证据生成中；这些流程会清除供应商凭据并隔离用户配置。只有同时指定环境变量和参数时才会执行：

```powershell
$env:MINICODE_LIVE_PROVIDER_SMOKE="1"
minicode-provider-smoke --run-live
```

## 网络安全与权限

模型可调用的 `web_fetch` 和 `http_request` 共用 `minicode.network_safety`：

- 仅接受 `http://` 与 `https://`；拒绝 URL 内嵌用户名或密码。
- 域名解析出的每一个地址都必须是公网全局地址；回环、私网、链路本地、保留、多播、元数据地址和异常数字编码地址会失败。
- 每次重定向重新验证目标，最多 5 次。
- 超时范围为 1–60 秒；请求体上限 100,000 字节；响应读取最多 200,000 字节，`http_request` 返回体进一步限制为 50,000 字节。
- `GET`/`HEAD` 在安全校验后按只读请求执行；`POST`、`PUT`、`PATCH`、`DELETE`、`OPTIONS` 必须逐次批准，不持久化“始终允许”。无交互审批器时默认拒绝。

失败示例：`http://127.0.0.1/`、`http://169.254.169.254/`、`http://user:pass@example.com/` 会返回明确错误；公网 URL 重定向到私网同样失败。

## Docker

镜像包含 `minicode/`、`Main/` 和 `Package/`，默认入口直接启动交互 CLI，不再默认执行 `--help`。

```powershell
docker build -t minicode-loop .
docker run --rm -it -e ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY -v "${PWD}:/workspace" minicode-loop
docker compose run --rm cli
docker compose run --rm headless "分析当前工作区"
```

Compose 仅提供 `cli` 与 `headless`。Gateway 与 Cron 已正式退休，不存在可用服务、命令或示例配置。

## 测试与质量门

pytest 自动发现根目录 `tests/test_*.py` 以及 `Main/`、`Package/` 下的 `*.Test.py`，统一使用 importlib 导入模式。结构测试在 Windows 创建真实 junction/reparse point，在 Unix 创建真实符号链接。

日常完整门禁：

```powershell
python -m pytest -q
python -m mypy minicode Main Package
python -m ruff check minicode Main Package tests
python -m compileall -q minicode tests benchmarks Main Package
python -m minicode.structure_check --root . --hotspots 5 --max-dependency-upstream 4 --check-material-inventory --report .temp/structure-compliance.json
python -m minicode.release_readiness --check-structure-compliance-artifact .temp/structure-compliance.json
```

Readiness 与证据门（不会调用真实模型供应商）：

```powershell
python -m minicode.readiness --json --fail-on blocked
python -m minicode.readiness --examples-out .temp/readiness-fallback-examples.json --fail-on blocked
python -m minicode.readiness --doctor-out .temp/readiness-doctor.md --fail-on blocked
python -m minicode.readiness --repair-plan-out .temp/readiness-repair-plan.json --fail-on blocked
python -m minicode.readiness --patch-preview-out .temp/readiness-fallback-patch-preview.json --fail-on blocked
python -m minicode.readiness --bundle-out .temp/readiness-bundle --fail-on blocked
python -m minicode.release_readiness --check-artifact-manifest .temp/readiness-artifact-manifest.json
python -m minicode.release_readiness --check-fallback-patch-preview .temp/readiness-fallback-patch-preview.json
python -m minicode.release_readiness --check-fallback-simulation .temp/readiness-bundle/readiness-fallback-simulations.json
python -m minicode.release_readiness --check-fallback-switch-smoke
python -m minicode.release_readiness --check-readiness-bundle .temp/readiness-bundle
python -m minicode.release_readiness --check-fallback-evidence benchmarks/release_readiness_results.json
python -m minicode.release_readiness --check-release-report benchmarks/release_readiness_results.json
python -m minicode.release_readiness --check-release-markdown benchmarks/release_readiness_results.md --release-json benchmarks/release_readiness_results.json
```

构建与隔离安装：

```powershell
python -m build
python -m pip install --force-reinstall --no-deps dist/minicode_loop-*.whl
minicode-py --help
minicode-headless --help
minicode-readiness --help
minicode-structure-check --help
minicode-provider-smoke --help
```

## 目录

```text
minicode/                         当前运行包
Main/MinicodeFrontline/          产品入口投影及镜像测试（内部兼容路径）
Package/EngineeringStructure/    结构扫描器及镜像测试
tests/                            核心安全与交付回归
benchmarks/                       可复现评估与发布证据
outputs/                          规范化评估输出
Docs/Documentation/              当前文档与带日期历史资料
```

当前结构与实现职责见 [STRUCTURE.md](Docs/Documentation/STRUCTURE.md)，操作细节见 [USAGE_GUIDE.md](Docs/Documentation/USAGE_GUIDE.md)，集成边界见 [INTEGRATION_GUIDE.md](Docs/Documentation/INTEGRATION_GUIDE.md)。`README.zh-CN.md` 是可选镜像；本文件是唯一必需的根文档。
