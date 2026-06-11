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
- Task 5 提交：`c5cf740 Add API demo flow`。
- Task 6 开始：补页面路由 smoke test，再实现 7 个页面路由、Jinja 模板、移动端 CSS 和轻量 JS 交互。
- Task 6 调试：当前 Starlette `TemplateResponse` 签名为 `TemplateResponse(request, name, context)`，已按实际签名修正页面渲染。
- Task 6 浏览器验证：in-app Browser 当前不可用，改用 Playwright CLI 在 390px 宽度完成 `login -> upload -> confirm -> pillbox -> reminders -> taken -> qa red question`。
- Task 6 修正：提醒时间展示从 `planned_at` 改为 `time_of_day`，避免 UTC 转本地后 08:00 显示成 16:00；服药状态从英文值映射为中文展示。
- Task 6 验证：`pytest tests/test_pages.py -q` 通过 1 项页面测试；`pytest -q` 通过 15 项测试；Playwright 控制台 0 error / 0 warning。
- Task 6 提交：`974c299 Add mobile demo UI`。
- Task 7/8 开始：补 `.dockerignore`、`Dockerfile`、`docker-compose.yml`、`Caddyfile`，并同步 README、API、测试和截图文档。
- Task 7/8 验证：`pytest -q` 通过 15 项测试；`git diff --check` 通过；`docker compose config` 通过。
- Task 7/8 Docker 验证：首次 `docker compose up -d --build` 发现 Docker daemon 未启动，已启动 Docker Desktop 后重跑成功；`docker compose ps` 显示 `app`、`postgres`、`caddy` 运行，`postgres` healthy；`docker compose logs --tail=100 app` 无 traceback；`curl -k https://localhost/login` 返回登录页内容。
- Task 9 review：按 requesting-code-review 调用子代理做只读审查。审查指出 MiniMax 配置后失败可能 500、过敏诊断问题未红色拒答、前端动态 HTML 未转义、手动 Pydantic 校验可能 500、缺少 `docs/product/mvp-scope.md`。
- Task 9 修复：MiniMax 客户端异常统一包装为 `RuntimeError`；红色风险覆盖加量、胸痛继续吃、停药、药物过敏判断；API 无效 payload 返回 422；前端动态输出加 HTML 转义；新增 `docs/product/mvp-scope.md` 并白名单 `docs/product/`。
- Task 9 修复：提醒计划和 7 天摘要改为默认按 `Asia/Shanghai` 计算，避免 Docker UTC 日期影响中国用户 Demo。
- Task 9 修复：QA 页有药品时默认选中第一条药品；测试夹具每次重建内存表，避免测试之间共享药品记录。
- Task 9 验证：关键回归组 `pytest tests/test_safety.py tests/test_ai_schema.py tests/test_api_flow.py -q` 通过 14 项测试；记录/API 回归组 `pytest tests/test_records.py tests/test_api_flow.py -q` 通过 5 项测试；页面/API 回归组 `pytest tests/test_pages.py tests/test_api_flow.py -q` 通过 4 项测试；全量 `.venv/bin/pytest -q` 通过 20 项测试；`git diff --check` 通过。
- Task 9 最终浏览器烟测：Playwright 390px 视口完成登录、上传、确认、药箱、提醒“已服”、QA 普通问题来源回答、QA 高风险 red 拒答；7 天摘要按 `Asia/Shanghai` 显示到 `2026-06-12`；控制台 0 error / 0 warning。
