# MiniCode Loop 后续改进计划

状态日期：2026-09-11。

## 本轮已落实

- [x] 公共 HTTP(S) 网络安全层：地址分类、DNS 全结果校验、逐跳重定向复验、跳数/超时/请求体/响应体上限。
- [x] 网络权限：GET/HEAD 只读；POST/PUT/PATCH/DELETE/OPTIONS 一次性授权；非交互环境失败关闭。
- [x] Docker 构建完整包含 `minicode/`、`Main/`、`Package/`，默认进入 CLI；Compose 仅保留 `cli` 与 `headless`。
- [x] Gateway/Cron 从当前服务、变量、示例和文档入口退休。
- [x] pytest 自动发现根测试和 `Main/Package` 的 `*.Test.py`，使用 importlib 模式，并验证 Windows junction/Unix symlink。
- [x] mypy namespace package 解析启用，现行检查范围零错误；没有全局忽略、基线或规则放宽。
- [x] Ruff 检查范围零告警。
- [x] 运行路径中原有的静默宽泛异常已改为有上下文日志；顶层安全网仍把失败转换为稳定结果。
- [x] 开发依赖包含 pytest、Hypothesis、mypy、Ruff、build 与 setuptools。
- [x] README、结构、使用、集成、代码百科、产品投影和材料清单同步到当前行为。
- [x] 材料扫描器将 README 中文镜像改为可选，并加入公开入口、退休服务、路径和命令目标一致性检查。

## 仍可继续的工作

- [ ] 在实际安装 Docker 的 Windows/Linux 主机上执行镜像构建矩阵；当前仓库测试只做确定性的 Dockerfile/Compose 配置验证。
- [ ] 在获得用户明确授权和真实凭据后运行 `minicode-provider-smoke --run-live`；默认验收和发布证据生成不调用供应商，缺失诊断只记录离线失败证据。
- [ ] 增加 CI 服务配置，使 Python 3.11/3.12、Windows/Linux 的同一质量门自动执行。
- [ ] 为 DNS 解析到连接之间的竞态增加传输层地址固定方案；当前每次初始 URL 和每个重定向都会重新做完整公共地址校验。
- [ ] 逐步为仍未注解的内部控制器补齐函数签名；这不是当前 mypy 错误，但可提高未来严格模式覆盖率。

## 不在计划内

- 不恢复 `.git`、旧测试树或已删除的比较源码。
- 不重新实现 Gateway/Cron。
- 不通过 mock、skip 或真实供应商调用制造发布通过状态。
- 不按文件大小机械拆分核心模块；后续拆分必须基于明确职责和测试证据。

## 当前验收命令

```powershell
python -m pytest -q
python -m mypy minicode Main Package
python -m ruff check minicode Main Package tests
python -m compileall -q minicode tests benchmarks Main Package
python -m minicode.structure_check --root . --check-material-inventory
python -m build
```
