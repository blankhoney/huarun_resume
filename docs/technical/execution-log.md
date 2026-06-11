# 执行日志

## 2026-06-12

- 启动执行 `docs/technical/implementation-plan.md`。
- 按用户要求在当前仓库工作；当前 checkout 位于 `main`，不是 linked worktree。
- 约束：不提交 `.env`、`.agents/`、`AGENTS.md`、`prd.docx`、上传图片、截图和私有笔记。
- Task 1 开始：更新 Git 可见性、创建 Python 包骨架、README 和 smoke test。
- 本机系统 Python 触发 PEP 668 externally-managed-environment，已确认根因是环境保护策略；改用项目本地 `.venv` 执行依赖安装和测试。
- Task 1 验证：`.venv` 依赖安装完成，`pytest -q` 通过 1 项 smoke test。
- Task 1 调整：显式忽略 `.venv/`、`.pytest_cache/`、`__pycache__/` 和 Python egg-info，避免 Git ignored 检查输出依赖目录细节。
- Task 1 提交：`d8b7671 Add MVP scaffold`。
- Task 2 开始：先补 `MedicineExtraction`、`ConfirmMedicinePayload` 和安全分级测试，再实现合同层。
- Task 2 验证：`pytest tests/test_ai_schema.py tests/test_safety.py -q` 通过 6 项测试。
- Task 2 提交：`7e0b6c3 Add safety schemas`。
- Task 3 开始：先补记录统计和 SQLite 内存库建表测试，再实现设置、数据库、模型、Demo 常量和记录统计 helper。
- Task 3 验证：`pytest tests/test_records.py -q` 通过 2 项测试；`pytest -q` 通过 9 项测试。
- Task 3 提交：`5e96cdb Add medication data model`。
- Task 4 开始：扩展 AI schema 测试，覆盖 thinking tag 清理、Demo 兜底抽取、红色拒答和无 key 来源兜底问答。
- Task 4 验证：`pytest tests/test_ai_schema.py tests/test_safety.py -q` 通过 10 项测试；`pytest -q` 通过 13 项测试。
- Task 4 提交：`8fb4995 Add AI workflow fallback`。
- Task 5 开始：补 FastAPI TestClient 集成测试，覆盖登录、上传、确认、药箱、今日提醒、服药记录、红色问答和无 key 绿色问答兜底。
- Task 5 验证：`pytest tests/test_api_flow.py tests/test_records.py -q` 通过 3 项测试；`pytest -q` 通过 14 项测试。当前仅有 Starlette/FastAPI TestClient 的上游弃用警告。
