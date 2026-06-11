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

## 2026-06-12 Review Fixes

- 按 Superpowers 流程创建隔离 worktree：`.worktrees/mvp-review-fixes`，分支 `mvp-review-fixes`。
- 基线验证：`../../.venv/bin/pytest -q` 通过 20 项测试；首次命令路径写成 `../.venv/bin/pytest` 失败，根因是 worktree 位于 `.worktrees/mvp-review-fixes`，已改为 `../../.venv/bin/pytest`。
- 上传安全 TDD：先补 `tests/test_upload_security.py`，确认伪造 HTML、超限上传和私有读取测试失败；实现真实 JPG/PNG 校验、5MB 限制、服务端生成文件名、登录态 `/uploads/{user_id}/{filename}` 读取接口；将测试 PNG 夹具修正为合法 PNG CRC。
- 上传安全 review：subagent 只读审查无 Critical/Important；按建议补跨用户图片访问回归测试。
- 幂等 TDD：先补 `tests/test_idempotency.py`，确认重复 confirm 和重复 dose record 失败；实现同 scan 重复确认返回既有药品和提醒，同 schedule + planned_at 重复记录更新原记录。
- 幂等 review：subagent 发现非升序提醒时间下重复 confirm 返回顺序不一致，以及缺少数据库唯一约束；已补失败测试并修复为按 `ReminderSchedule.id` 返回，同时为 `medicines.scan_id` 和 `dose_records(schedule_id, planned_at)` 增加唯一约束。
- QA/summary TDD：先补 MiniMax 异常 `sources` schema 测试和 `records/summary` 的 `days=0/31` 边界测试；实现 `QaModelAnswer` 校验、sources 清理和最多 3 条限制，`days` 改为 1 到 30。
- QA/summary review：subagent 只读审查无 Critical/Important/Minor。
- 生产配置 TDD：先补 `tests/test_settings.py`，确认缺少生产校验入口；实现 `APP_ENV=production` 时拒绝默认数据库凭据、默认 session secret 和默认 Demo 密码，生产环境 session cookie 开启 `https_only`。
- Docker Compose 修复：`POSTGRES_PASSWORD`、`DATABASE_URL`、`SESSION_SECRET`、`DEMO_PASSWORD` 改为必填；`APP_ENV` 默认 `production`。验证缺失变量时 `docker compose config` 失败，显式提供变量时通过。
- 文档同步：README、接口文档、测试文档、技术选型、产品设计、用户旅程、截图清单和执行计划统一为“当前 MVP 使用固定 Demo 文本，不执行真实 OCR”，并更新生产 `.env` 模板。
- 生产配置/文档 review：subagent 指出 README `replace-with-*` 占位符仍会被生产校验接受，以及 `docs/product/mvp-scope.md` 仍有“图片无法识别时”旧表述；已补 placeholder 失败测试、扩展生产校验并修正文档。
- 自查补充：Pillow 对损坏 PNG CRC 会抛 `SyntaxError`，已补回归测试并统一返回 415。
- 当前全量验证：`../../.venv/bin/pytest -q` 通过 33 项测试，保留 1 条上游 TestClient deprecation warning；`git diff --check` 通过；显式提供生产变量时 `docker compose config` 通过。
- Docker 验证：使用 `docker compose -p huarun-mvp-fix up -d --build app` 启动临时 `postgres` 和 `app`，`postgres` healthy，`app` running；`docker compose logs --tail=100 app` 无 traceback；在 app 容器内请求 `http://127.0.0.1:8000/login` 返回 200 且包含 `AI 用药伴侣`。为避免端口和资源占用，验证后执行 `docker compose -p huarun-mvp-fix down` 停止临时栈。
