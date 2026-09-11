# MiniCode Loop 产品表面投影

审计日期：2026-09-11。逻辑边界为 `Main/MinicodeFrontline`（MiniCode Loop 的内部兼容投影），当前源码根为 `minicode/`；Python 包路径保持 `minicode` 以兼容现有安装。

## 可运行表面

| 表面 | 入口 | 代码所有者 | 覆盖证据 |
| --- | --- | --- | --- |
| 交互 CLI/TUI | `minicode-py`, `python -m minicode.main` | `minicode/main.py`, `minicode/tty_app.py`, `minicode/tui/` | `tests/test_delivery_surfaces.py`, `Main/MinicodeFrontline/Test/Application/Entry/MiniCodeFrontline.Test.py` |
| Headless | `minicode-headless`, `python -m minicode.headless` | `minicode/headless.py` | `tests/test_delivery_surfaces.py` |
| Readiness | `minicode-readiness`, `python -m minicode.readiness` | `minicode/readiness.py`, `minicode/product_surfaces.py` | Main Query 镜像测试 |
| Structure Check | `minicode-structure-check`, `python -m minicode.structure_check` | `Package/EngineeringStructure`, `minicode/structure_check.py` | Package Query 镜像测试 |
| Provider Smoke | `minicode-provider-smoke`, `python -m minicode.provider_smoke` | `minicode/provider_smoke.py` | `tests/test_delivery_surfaces.py`；真实请求需显式授权 |

Gateway/Cron 为已退休表面，不在产品依赖图、包入口或 Compose 中。

## 安全投影

`web_fetch` 和 `http_request` 通过 `minicode/network_safety.py` 进入同一公共网络边界。该边界只允许 HTTP/HTTPS，拒绝凭据和所有非全局 IP，验证 DNS 的全部结果，并在最多 5 次重定向中逐跳复验。`PermissionManager.ensure_network_request` 对非 GET/HEAD 方法执行一次性审批；无交互审批器时拒绝。

确定性覆盖位于 `tests/test_network_security.py`，包括回环、私网、链路本地、云元数据、IPv6 ULA、数字编码、凭据 URL、私网重定向、网络写授权、请求超时和响应截断。

## 工程结构投影

`Main/MinicodeFrontline` 暴露入口、DTO 和查询表面。`Package/EngineeringStructure` 提供产品根扫描和 Python 依赖边界。两者源码与测试目录精确镜像；根测试由 pytest 独立发现。

结构扫描拒绝符号链接、Windows junction/reparse point 和特殊载体。材料清单扫描同时检查当前文档、公开入口、退休服务、登记路径以及 `python -m` 命令目标。

## 材料清单

当前材料仅包括真实存在且仍有调用者或证据价值的三个根：

| 材料 | 状态 | 当前用途 |
| --- | --- | --- |
| `benchmarks/` | active-evidence | 发布、连续性和运行时评估证据 |
| `Docs/` | active-documentation | 当前文档与显式标记的历史记录 |
| `outputs/` | active-evidence | 规范化评估输出 |

权威机器清单为 `Docs/Documentation/engineering/material-inventory.json`。不存在的旧镜像、比较仓库、备份目录或测试文件不得继续登记为当前材料。

## 质量门和覆盖证据

```powershell
python -m pytest -q
python -m mypy minicode Main Package
python -m ruff check minicode Main Package tests
python -m compileall -q minicode tests benchmarks Main Package
python -m minicode.structure_check --root . --hotspots 5 --max-dependency-upstream 4 --check-material-inventory --report .temp/structure-compliance.json
python -m minicode.release_readiness --check-structure-compliance-artifact .temp/structure-compliance.json
python -m build
```

wheel 隔离安装后必须能启动五个公开命令的 `--help`。Dockerfile/Compose 由 `tests/test_delivery_surfaces.py` 验证；真实容器构建需在安装 Docker 的主机执行。默认验收和发布证据生成会清除供应商凭据、隔离用户配置，不调用真实模型供应商；缺失诊断保持为离线失败证据。

## 文档责任

任何公开入口、权限行为、安全限制、Docker 服务或质量门变化，都必须在同一工作单元更新 `README.md` 和相应专题文档。`README.zh-CN.md` 可选；中文 `README.md` 是唯一必需根文档。带日期的 `superpowers` 计划、规格和报告只保留历史语义，不作为当前实现依据。
