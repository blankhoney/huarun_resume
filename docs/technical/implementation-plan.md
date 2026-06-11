# AI 用药伴侣 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small, polished, deployable AI medication companion MVP for the 华润三九 interview task.

**Architecture:** Use one FastAPI service for server-rendered mobile pages and JSON APIs. PostgreSQL stores demo users, medicine scans, confirmed medicines, reminders, dose records, and QA logs. The MVP saves uploaded images but uses fixed Demo medicine text as the reproducible extraction input; MiniMax-M2.7 handles structured extraction and medication QA from that text, while Caddy terminates HTTPS on the Debian 13 VPS.

**Tech Stack:** Python 3.12, FastAPI, Jinja2, Vanilla JS, SQLAlchemy 2, PostgreSQL, OpenAI-compatible MiniMax client, pytest, Docker Compose, Caddy.

---

## Execution Status

- Status: implemented and under final verification on 2026-06-12.
- Commits produced: scaffold, safety schemas, data model, AI fallback workflow, API flow, mobile UI, VPS deployment config.
- Final review fixes: MiniMax client failures now enter fallback, red-risk allergy/diagnosis questions are refused, invalid API payloads return 422, dynamic UI output is HTML-escaped, and `docs/product/mvp-scope.md` records the MVP boundary.
- Intentional plan deviation: JSON API routes live in `src/huarun_app/main.py` to keep the MVP single-service and small; no separate `src/huarun_app/routers/api.py` was created.
- Demo boundary: upload saves the image, but the current test Demo uses fixed medicine text as reproducible fallback input. Real OCR/vision extraction is documented as the next product step, not part of this MVP.

---

## Review Decisions

- Keep the build intentionally small: 6 user-facing pages, 7 page routes, plus API docs; it is not a full medical platform.
- Use `docs/technical/implementation-plan.md` instead of `docs/superpowers/plans/...` because this repo only tracks selected public docs under `docs/technical/`.
- During design, only public docs are visible to Git. During implementation, Task 1 updates `.gitignore` to whitelist selected public source, tests, assets, and deployment files.
- Do not commit `.env`, `.env.*`, `AGENTS.md`, `.agents/`, uploaded images, generated screenshots, or private notes.
- Do not implement OCR in this MVP. Upload validates and stores JPG/PNG images, then uses fixed Demo medicine text so the interview demo always works.
- Do not build family sharing, SMS/WeChat push, native app notifications, doctor/pharmacist admin, payment, drug database ingestion, or medical diagnosis.

## File Map

- Modify `.gitignore`: during implementation only, allow MVP source, tests, deployment, assets, and public docs while keeping private files ignored.
- Create `README.md`: local run, deployment, demo account, environment variable table, demo script.
- Create `pyproject.toml`: dependencies and pytest config.
- Create `Dockerfile`, `docker-compose.yml`, `Caddyfile`: Debian VPS deployment.
- Create `src/huarun_app/main.py`: FastAPI app factory, static files, templates, router registration.
- Create `src/huarun_app/settings.py`: environment-driven settings.
- Create `src/huarun_app/database.py`: SQLAlchemy engine/session/create_all.
- Create `src/huarun_app/models.py`: database tables.
- Create `src/huarun_app/schemas.py`: Pydantic API and AI schemas.
- Create `src/huarun_app/demo_data.py`: demo account and deterministic medicine sample.
- Create `src/huarun_app/routers/pages.py`: HTML page routes.
- Keep JSON API routes in `src/huarun_app/main.py`: scan, confirm, pillbox, reminders, records, QA.
- Create `src/huarun_app/services/ai_client.py`: MiniMax OpenAI-compatible client wrapper.
- Create `src/huarun_app/services/medicine_ai.py`: scan extraction and QA workflow.
- Create `src/huarun_app/services/safety.py`: high-risk question classification.
- Create `src/huarun_app/services/records.py`: today's reminders and 7-day summary helpers.
- Create `src/huarun_app/templates/*.html`: login, home, upload/confirm, pillbox, reminders, QA.
- Create `assets/styles.css`, `assets/app.js`: mobile-first UI and small interactions.
- Create `tests/test_scaffold.py`, `tests/conftest.py`, `tests/test_ai_schema.py`, `tests/test_safety.py`, `tests/test_api_flow.py`, `tests/test_records.py`.
- Create `docs/requirements/user-journey-map.md`, `docs/product/mvp-scope.md`, `docs/technical/tech-selection.md`, `docs/technical/api.md`, `docs/technical/test-plan.md`, `docs/technical/screenshot-checklist.md`.

## Task 1: Repository Visibility And Python Scaffold

**Files:**
- Modify: `.gitignore`
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `src/huarun_app/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_scaffold.py`

- [ ] **Step 1: Update Git visibility rules**

Allow the implementation files that must be uploaded while keeping private files ignored:

```gitignore
# Public app source for the interview MVP.
!pyproject.toml
!Dockerfile
!docker-compose.yml
!Caddyfile
!src/
!src/**/*.py
!src/**/*.html
!tests/
!tests/**/*.py
!assets/
!assets/**/*.css
!assets/**/*.js

# Runtime-private generated data.
uploads/
screenshots/
*.sqlite3
```

- [ ] **Step 2: Add project metadata**

Create `pyproject.toml`:

```toml
[project]
name = "huarun-resume"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.34",
  "jinja2>=3.1",
  "python-multipart>=0.0.20",
  "sqlalchemy>=2.0",
  "psycopg[binary]>=3.2",
  "pydantic-settings>=2.7",
  "openai>=1.60",
  "pillow>=11.0",
  "itsdangerous>=2.2",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3",
  "httpx>=0.28",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 3: Add README skeleton**

`README.md` must include these sections: `项目目标`, `技术选型`, `本地运行`, `环境变量`, `测试账号`, `VPS 部署`, `Demo 演示脚本`, `面试截图清单`.

Environment variable table:

```markdown
| 变量 | 示例 | 说明 |
| --- | --- | --- |
| APP_ENV | production | 生产部署开启安全配置校验 |
| POSTGRES_PASSWORD | replace-with-strong-password | Docker Compose 中 PostgreSQL 密码 |
| DATABASE_URL | postgresql+psycopg://huarun:replace-with-strong-password@postgres:5432/huarun | PostgreSQL 连接串 |
| SESSION_SECRET | replace-with-32-plus-random-chars | session cookie 签名密钥 |
| MINIMAX_BASE_URL | https://api.minimax.io/v1 | MiniMax OpenAI-compatible 地址 |
| MINIMAX_API_KEY | sk-... | MiniMax key，仅放在服务器 `.env` |
| MINIMAX_MODEL | MiniMax-M2.7 | 文本结构化和问答模型 |
| DEMO_EMAIL | demo@blankhoney.xyz | 测试账号 |
| DEMO_PASSWORD | replace-with-demo-login-password | 测试密码，生产部署必须改掉默认值 |
```

- [ ] **Step 4: Add one scaffold smoke test**

Create `tests/test_scaffold.py`:

```python
def test_scaffold_imports_package():
    import huarun_app

    assert huarun_app is not None
```

- [ ] **Step 5: Verify scaffold**

Run:

```bash
python3 -m pip install -e ".[dev]"
pytest -q
git status --short --untracked-files=all
git status --short --ignored --untracked-files=all
git check-ignore -v AGENTS.md .agents/skills/using-superpowers/SKILL.md prd.docx .env docs/technical/implementation-plan.md README.md pyproject.toml
```

Expected:
- `pytest -q` reports `1 passed`.
- `AGENTS.md`, `.agents/...`, `prd.docx`, `.env` are ignored.
- `README.md`, `pyproject.toml`, `src/huarun_app/__init__.py`, `tests/test_scaffold.py`, and `docs/technical/implementation-plan.md` are not ignored after this task updates `.gitignore`.

## Task 2: Domain Schemas And Safety Rules

**Files:**
- Create: `src/huarun_app/schemas.py`
- Create: `src/huarun_app/services/safety.py`
- Create: `tests/test_ai_schema.py`
- Create: `tests/test_safety.py`

- [ ] **Step 1: Write schema tests**

`tests/test_ai_schema.py`:

```python
from huarun_app.schemas import MedicineExtraction


def test_medicine_extraction_requires_manual_confirmation_by_default():
    result = MedicineExtraction(
        drug_name="布洛芬缓释胶囊",
        generic_name="布洛芬",
        specification="0.3g*20粒",
        visible_dose_text="一次1粒，一日2次",
        frequency_suggestion="每日 08:00, 20:00",
        warnings=["胃肠道不适者遵医嘱"],
        source_quotes=["包装可见：布洛芬缓释胶囊 0.3g"],
        confidence=0.86,
    )

    assert result.needs_manual_confirmation is True
    assert result.fallback_used is False
```

`tests/test_safety.py`:

```python
from huarun_app.services.safety import classify_question


def test_red_question_is_refused():
    label = classify_question("我胸痛，可以自己加量继续吃吗？")
    assert label == "red"


def test_side_effect_question_is_yellow():
    label = classify_question("这个药头晕是不是副作用？")
    assert label == "yellow"


def test_packaging_question_is_green():
    label = classify_question("包装上写的一天几次？")
    assert label == "green"
```

- [ ] **Step 2: Verify tests fail first**

Run:

```bash
pytest tests/test_ai_schema.py tests/test_safety.py -q
```

Expected: fail with missing `huarun_app.schemas` or missing `classify_question`.

- [ ] **Step 3: Implement schemas and classifier**

`src/huarun_app/schemas.py`:

```python
from typing import Literal

from pydantic import BaseModel, Field

DoseStatus = Literal["taken", "later", "missed", "unwell"]
SafetyLabel = Literal["green", "yellow", "red"]


class MedicineExtraction(BaseModel):
    drug_name: str
    generic_name: str = ""
    specification: str = ""
    visible_dose_text: str = ""
    frequency_suggestion: str = "每日 08:00"
    warnings: list[str] = Field(default_factory=list)
    source_quotes: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    needs_manual_confirmation: bool = True
    fallback_used: bool = False


class ConfirmMedicinePayload(BaseModel):
    drug_name: str
    generic_name: str = ""
    specification: str = ""
    dose_text: str
    warning_text: str = ""
    reminder_times: list[str]
    confirmed: bool


class DoseRecordPayload(BaseModel):
    schedule_id: int
    status: DoseStatus
    note: str = ""


class QaPayload(BaseModel):
    medicine_id: int
    question: str
```

`src/huarun_app/services/safety.py`:

```python
from huarun_app.schemas import SafetyLabel

RED_KEYWORDS = ("加量", "减量", "停药", "换药", "胸痛", "呼吸困难", "昏迷", "严重过敏", "急救")
YELLOW_KEYWORDS = ("副作用", "头晕", "漏服", "忘吃", "能一起吃", "不舒服", "不适")


def classify_question(question: str) -> SafetyLabel:
    if any(keyword in question for keyword in RED_KEYWORDS):
        return "red"
    if any(keyword in question for keyword in YELLOW_KEYWORDS):
        return "yellow"
    return "green"
```

- [ ] **Step 4: Verify tests pass**

Run:

```bash
pytest tests/test_ai_schema.py tests/test_safety.py -q
```

Expected: `4 passed`.

- [ ] **Step 5: Commit**

Run the Git visibility checks from Task 1, then:

```bash
git add .gitignore README.md pyproject.toml src/huarun_app tests
git commit -m "Add MVP scaffold and safety schemas"
```

## Task 3: Database Models And Demo Data

**Files:**
- Create: `src/huarun_app/settings.py`
- Create: `src/huarun_app/database.py`
- Create: `src/huarun_app/models.py`
- Create: `src/huarun_app/demo_data.py`
- Create: `src/huarun_app/services/records.py`
- Create: `tests/test_records.py`

- [ ] **Step 1: Write records test**

`tests/test_records.py`:

```python
from datetime import datetime, timedelta, timezone

from huarun_app.services.records import summarize_records


def test_summarize_records_counts_last_seven_days():
    now = datetime(2026, 6, 12, 8, 0, tzinfo=timezone.utc)
    records = [
        {"planned_at": now, "status": "taken"},
        {"planned_at": now - timedelta(days=1), "status": "missed"},
        {"planned_at": now - timedelta(days=1), "status": "unwell"},
        {"planned_at": now - timedelta(days=8), "status": "taken"},
    ]

    summary = summarize_records(records, now=now, days=7)

    assert summary["totals"] == {"taken": 1, "later": 0, "missed": 1, "unwell": 1}
    assert len(summary["days"]) == 7
```

- [ ] **Step 2: Verify test fails first**

Run:

```bash
pytest tests/test_records.py -q
```

Expected: fail with missing `summarize_records`.

- [ ] **Step 3: Implement settings, DB, models, and summary helper**

Required models:
- `User`: `id`, `email`, `password_hash`, `name`, `created_at`
- `MedicineScan`: `id`, `user_id`, `image_path`, `raw_text`, `extraction_json`, `fallback_used`, `created_at`
- `Medicine`: `id`, `user_id`, `scan_id`, `drug_name`, `generic_name`, `specification`, `dose_text`, `warning_text`, `source_quotes_json`, `confidence`, `confirmed_at`
- `ReminderSchedule`: `id`, `medicine_id`, `time_of_day`, `active`
- `DoseRecord`: `id`, `schedule_id`, `planned_at`, `status`, `recorded_at`, `note`
- `QaLog`: `id`, `user_id`, `medicine_id`, `question`, `answer`, `safety_label`, `source_quotes_json`, `created_at`

`database.py` must support two URLs:
- PostgreSQL for local/VPS: `postgresql+psycopg://...`
- Test SQLite memory DB: `sqlite+pysqlite:///:memory:` with `StaticPool` and `check_same_thread=False`

`summarize_records()` must ignore records older than the requested window and return this shape:

```python
{
    "totals": {"taken": 1, "later": 0, "missed": 1, "unwell": 1},
    "days": [
        {"date": "2026-06-06", "taken": 0, "later": 0, "missed": 0, "unwell": 0}
    ],
}
```

- [ ] **Step 4: Add demo constants**

`src/huarun_app/demo_data.py` must define:
- `DEMO_EMAIL = "demo@blankhoney.xyz"`
- `DEMO_PASSWORD = "Demo123456!"`
- `DEMO_MEDICINE_TEXT = "药品名称：布洛芬缓释胶囊。规格：0.3g*20粒。用法用量：成人一次1粒，一日2次，早晚服用。本品可能引起胃部不适、恶心、头晕。对本品过敏者禁用，严重不适请咨询医生或药师。"`
- `DEMO_EXTRACTION` as `MedicineExtraction(drug_name="布洛芬缓释胶囊", generic_name="布洛芬", specification="0.3g*20粒", visible_dose_text="成人一次1粒，一日2次，早晚服用", frequency_suggestion="每日 08:00, 20:00", warnings=["可能引起胃部不适、恶心、头晕", "对本品过敏者禁用"], source_quotes=["药品名称：布洛芬缓释胶囊", "用法用量：成人一次1粒，一日2次"], confidence=0.86, needs_manual_confirmation=True, fallback_used=True)`.

- [ ] **Step 5: Verify records test**

Run:

```bash
pytest tests/test_records.py -q
```

Expected: `1 passed`.

- [ ] **Step 6: Commit**

Run Git visibility checks, then:

```bash
git add src/huarun_app tests/test_records.py
git commit -m "Add medication data model"
```

## Task 4: AI Workflow Service

**Files:**
- Create: `src/huarun_app/services/ai_client.py`
- Create: `src/huarun_app/services/medicine_ai.py`
- Modify: `tests/test_ai_schema.py`

- [ ] **Step 1: Extend AI tests**

Add tests for cleaning thinking tags, fallback behavior, and red-question refusal:

```python
from huarun_app.services.medicine_ai import (
    answer_medicine_question,
    clean_model_text,
    fallback_extraction,
    refusal_answer,
)


def test_clean_model_text_removes_think_tags():
    text = "<think>internal</think>{\"drug_name\":\"布洛芬\"}"
    assert clean_model_text(text) == "{\"drug_name\":\"布洛芬\"}"


def test_fallback_extraction_is_marked():
    result = fallback_extraction()
    assert result.fallback_used is True
    assert result.needs_manual_confirmation is True
    assert result.drug_name


def test_refusal_answer_contains_doctor_guidance():
    answer = refusal_answer("我可以自己加量吗？")
    assert answer["safety_label"] == "red"
    assert "医生" in answer["answer"] or "药师" in answer["answer"]


def test_qa_fallback_uses_sources_when_model_is_unavailable():
    answer = answer_medicine_question(
        "包装上写的一天几次？",
        "用法用量：成人一次1粒，一日2次，早晚服用。",
    )
    assert answer["safety_label"] == "green"
    assert answer["sources"]
    assert "医生" in answer["answer"] or "说明书" in answer["answer"]
```

- [ ] **Step 2: Verify tests fail first**

Run:

```bash
pytest tests/test_ai_schema.py -q
```

Expected: fail with missing service functions.

- [ ] **Step 3: Implement MiniMax client wrapper**

`ai_client.py` must:
- Create `OpenAI(base_url=settings.minimax_base_url, api_key=settings.minimax_api_key)`.
- Use `client.chat.completions.create(model=settings.minimax_model, messages=...)`.
- Return only `response.choices[0].message.content`.
- If `MINIMAX_API_KEY` is empty, raise `RuntimeError("MiniMax API key is not configured")`; workflow functions must catch this and return their fallback response.

- [ ] **Step 4: Implement medicine AI workflow**

`medicine_ai.py` must expose:
- `clean_model_text(text: str) -> str`
- `fallback_extraction() -> MedicineExtraction`
- `extract_medicine_info(raw_text: str) -> MedicineExtraction`
- `answer_medicine_question(question: str, medicine_context: str) -> dict`
- `refusal_answer(question: str) -> dict`
- `source_fallback_answer(question: str, medicine_context: str, safety_label: str) -> dict`

System prompt rules:

```text
你是“AI 用药伴侣”的药品信息整理助手。只能抽取和解释用户上传包装、说明书或系统提供文本中的信息。不得编造药名、剂量、频次、疗程、禁忌或适应症。不得建议用户自行加量、减量、停药、换药或合并用药。涉及胸痛、呼吸困难、严重过敏、意识障碍等高风险问题时，必须建议立即联系医生、药师或急救。输出必须是 JSON。
```

Fallback rule:
- Empty raw text, model error, JSON parse error, missing `drug_name`, or confidence outside `0..1` returns `fallback_extraction()`.
- For QA, red questions return `refusal_answer()` without calling MiniMax. Green and yellow questions call MiniMax when configured; if the key is empty, network fails, or the response cannot be parsed, return `source_fallback_answer()` with `sources` extracted from the current medicine context and `safety_label` preserved.

- [ ] **Step 5: Verify AI service tests**

Run:

```bash
pytest tests/test_ai_schema.py tests/test_safety.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

Run Git visibility checks, then:

```bash
git add src/huarun_app/services tests/test_ai_schema.py
git commit -m "Add MiniMax medicine AI workflow"
```

## Task 5: FastAPI APIs

**Files:**
- Create: `src/huarun_app/main.py`
- Create: `src/huarun_app/routers/api.py`
- Create: `tests/conftest.py`
- Create: `tests/test_api_flow.py`

- [ ] **Step 1: Add test app fixture**

`tests/conftest.py`:

```python
import os

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["SESSION_SECRET"] = "test-session-secret"
os.environ["MINIMAX_API_KEY"] = ""


@pytest.fixture()
def client():
    from huarun_app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
```

- [ ] **Step 2: Write API flow test**

`tests/test_api_flow.py` must verify:
- Demo login returns 200.
- Uploading a generated PNG to `/api/medicines/scan` returns `scan_id` and an extraction.
- Confirming the scan creates a medicine.
- `/api/pillbox` returns the confirmed medicine.
- `/api/reminders/today` returns at least one reminder.
- Posting a `taken` dose record succeeds.
- Posting a red QA question returns `safety_label="red"`.
- Posting a green QA question with `MINIMAX_API_KEY=""` still returns HTTP 200 and at least one source quote.

- [ ] **Step 3: Verify test fails first**

Run:

```bash
pytest tests/test_api_flow.py -q
```

Expected: fail with missing app or routes.

- [ ] **Step 4: Implement API endpoints**

Endpoints:
- `POST /api/auth/demo-login`
- `POST /api/medicines/scan`
- `POST /api/medicines/{scan_id}/confirm`
- `GET /api/pillbox`
- `GET /api/reminders/today`
- `POST /api/dose-records`
- `POST /api/qa`
- `GET /api/records/summary?days=7`

Behavior constraints:
- `confirm` rejects `confirmed=false` with HTTP 400.
- `scan` accepts only `image/jpeg` and `image/png`.
- `qa` always stores `question`, `answer`, `safety_label`, and `source_quotes`.
- Red QA returns refusal text and never calls MiniMax.
- Green and yellow QA catch MiniMax failures and return source-based fallback answers rather than HTTP 500.

- [ ] **Step 5: Verify API tests**

Run:

```bash
pytest tests/test_api_flow.py tests/test_records.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

Run Git visibility checks, then:

```bash
git add src/huarun_app tests/test_api_flow.py
git commit -m "Add medication companion APIs"
```

## Task 6: Server-Rendered Mobile UI

**Files:**
- Create: `src/huarun_app/routers/pages.py`
- Create: `src/huarun_app/templates/base.html`
- Create: `src/huarun_app/templates/login.html`
- Create: `src/huarun_app/templates/index.html`
- Create: `src/huarun_app/templates/upload.html`
- Create: `src/huarun_app/templates/confirm.html`
- Create: `src/huarun_app/templates/pillbox.html`
- Create: `src/huarun_app/templates/reminders.html`
- Create: `src/huarun_app/templates/qa.html`
- Create: `assets/styles.css`
- Create: `assets/app.js`

Canonical page scope: 6 user-facing pages and 7 routes. `/upload` and `/confirm/{scan_id}` are separate route steps in the same add-medicine workflow.

- [ ] **Step 1: Add page routes**

Routes:
- `GET /login`
- `GET /`
- `GET /upload`
- `GET /confirm/{scan_id}`
- `GET /pillbox`
- `GET /reminders`
- `GET /qa`

- [ ] **Step 2: Implement visual system**

CSS requirements:
- Mobile container max width `520px`, centered on desktop.
- Body font size at least `18px`.
- Primary action buttons min height `52px`.
- Cards border radius no more than `8px`.
- Use at least three state colors: green for taken, amber for later, red for missed/unwell.
- Avoid one-note purple/blue gradients and decorative blobs.

- [ ] **Step 3: Implement core pages**

Page requirements:
- Login: demo account hint and privacy notice.
- Home: three large entries: `拍照添加药品`, `今日提醒`, `问一问`.
- Upload: image preview, upload button, clear text for photo requirements.
- Confirm: editable drug fields, source quotes, manual confirmation checkbox, reminder time inputs.
- Pillbox: medicine card with image, drug name, reminder time, today status, QA link.
- Reminders: one reminder focus area with four large buttons: `已服`, `稍后`, `漏服`, `不适`; same page includes 7-day summary.
- QA: common question buttons, input area, answer block, source block, safety label.

- [ ] **Step 4: Add light JavaScript interactions**

`assets/app.js` must handle:
- Upload preview.
- Calling scan API then redirecting to `/confirm/{scan_id}`.
- Submitting confirm form.
- Posting dose status.
- Posting QA question and rendering answer/sources.
- Demo one-minute countdown text on reminders page.

- [ ] **Step 5: Manual UI verification**

Run:

```bash
uvicorn huarun_app.main:app --reload
```

Open `http://127.0.0.1:8000` and complete:
`login -> upload -> confirm -> pillbox -> reminders -> taken -> qa red question`.

Expected:
- No overlapping text at 390px width.
- Buttons are thumb-sized.
- Red question refuses medical advice.
- Demo flow remains usable when MiniMax key is missing.

- [ ] **Step 6: Commit**

Run Git visibility checks, then:

```bash
git add src/huarun_app/templates assets src/huarun_app/routers/pages.py src/huarun_app/main.py
git commit -m "Add mobile demo interface"
```

## Task 7: Public Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/requirements/user-journey-map.md`
- Create: `docs/technical/tech-selection.md`
- Create: `docs/technical/api.md`
- Create: `docs/technical/test-plan.md`
- Create: `docs/technical/screenshot-checklist.md`

- [ ] **Step 1: Write user journey map**

Include this table:

```markdown
| 阶段 | 用户目标 | 触点 | 风险 | MVP 设计 |
| --- | --- | --- | --- | --- |
| 初次进入 | 快速知道能做什么 | 登录页、首页 | 表单太多导致放弃 | 测试账号和三个主入口 |
| 拍照上传 | 少手动输入 | 上传页 | 图片模糊、识别错 | 图片预览和可重传 |
| AI 识别 | 看懂包装信息 | 确认页 | 模型编造剂量 | 来源片段和置信度 |
| 人工确认 | 防止错药错量 | 确认勾选 | 未确认直接提醒 | 未勾选禁止保存 |
| 电子药箱 | 看到正在吃什么 | 药箱卡片 | 药品混淆 | 图片、药名、时间 |
| 定时提醒 | 到点记录状态 | 提醒页 | Web 通知不稳定 | Demo 倒计时和页面提醒 |
| 服药记录 | 一键完成 | 四个状态按钮 | 操作复杂 | 大按钮和时间戳 |
| 用药问答 | 解释说明文字 | QA 页 | 危险建议 | 来源引用和红色拒答 |
```

- [ ] **Step 2: Write tech selection**

Explain:
- FastAPI single app is enough for a 1-3 day interview MVP.
- PostgreSQL gives realistic persistence without adding Redis/Celery.
- Caddy is used for automatic HTTPS and simple reverse proxy.
- MiniMax-M2.7 is used for text structuring and QA; vision is not assumed.
- Fixed Demo text fallback protects demo reliability while real OCR stays outside MVP scope.

- [ ] **Step 3: Write API docs**

For each API, document method, path, purpose, request, response, and failure case. Include exact examples for scan, confirm, dose record, green QA, and red QA. The QA docs must state that model failure returns a conservative source-based fallback for green/yellow questions.

- [ ] **Step 4: Write test plan**

Include:
- `pytest -q`
- `git diff --check`
- full API flow scenario
- mobile UI scenario
- VPS smoke test
- high-risk QA safety cases

- [ ] **Step 5: Write screenshot checklist**

Required screenshots:
- System prompt in `medicine_ai.py`.
- `MedicineExtraction` schema in `schemas.py`.
- AI workflow functions in `medicine_ai.py`.
- FastAPI API routes in `routers/api.py`.
- `docker-compose.yml` and `Caddyfile`.
- UI: home, scan confirm, pillbox, reminders, QA refusal.

- [ ] **Step 6: Commit**

Run Git visibility checks, then:

```bash
git add README.md docs/requirements docs/technical
git commit -m "Document MVP interview deliverables"
```

## Task 8: Docker Compose And Caddy Deployment

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `Caddyfile`
- Modify: `README.md`

- [ ] **Step 1: Add Dockerfile**

Required behavior:
- Base image `python:3.12-slim`.
- Install package with `pip install .`.
- Set `PYTHONPATH=/app/src`.
- Expose `8000`.
- Command: `uvicorn huarun_app.main:app --host 0.0.0.0 --port 8000`.

- [ ] **Step 2: Add Compose services**

Services:
- `postgres`: `postgres:17`, volume `postgres_data`, env values scoped to demo.
- `app`: build current directory, depends on postgres, mounts `uploads_data:/app/uploads`.
- `caddy`: `caddy:2`, ports `80:80`, `443:443`, mounts `Caddyfile`, `caddy_data`, `caddy_config`.

- [ ] **Step 3: Add Caddyfile**

Use a replaceable domain placeholder:

```caddyfile
{$DEMO_DOMAIN} {
  reverse_proxy app:8000
}
```

- [ ] **Step 4: Add VPS deployment instructions**

README deployment commands:

```bash
cat > .env <<'EOF'
DEMO_DOMAIN=huarun-demo.blankhoney.xyz
APP_ENV=production
POSTGRES_PASSWORD=replace-with-strong-password
DATABASE_URL=postgresql+psycopg://huarun:replace-with-strong-password@postgres:5432/huarun
SESSION_SECRET=replace-with-32-plus-random-chars
MINIMAX_BASE_URL=https://api.minimax.io/v1
MINIMAX_API_KEY=replace-on-server-only
MINIMAX_MODEL=MiniMax-M2.7
DEMO_EMAIL=demo@blankhoney.xyz
DEMO_PASSWORD=replace-with-demo-login-password
EOF
docker compose up -d --build
docker compose logs -f app
```

Because `.env.*` is ignored in this repo, write the `.env` contents as a README block named "服务器环境变量模板" rather than committing an `.env.example` file.

Deployment DNS target: create an `A` record for `huarun-demo.blankhoney.xyz` pointing to `43.130.244.175`. Do not use `huarun_demo.blankhoney.xyz` as the Caddy automatic HTTPS host because the underscore can prevent public TLS certificate issuance.

- [ ] **Step 5: Verify deployment locally**

Run:

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 app
```

Expected:
- Config renders without invalid interpolation.
- `app`, `postgres`, and `caddy` are running.
- App logs show startup without traceback.

- [ ] **Step 6: Commit**

Run Git visibility checks, then:

```bash
git add Dockerfile docker-compose.yml Caddyfile README.md
git commit -m "Add VPS deployment configuration"
```

## Task 9: Final Verification And Interview Package

**Files:**
- Modify: `README.md`
- Modify: `docs/technical/test-plan.md`
- Modify: `docs/technical/screenshot-checklist.md`

- [ ] **Step 1: Run local verification**

Run:

```bash
pytest -q
git diff --check
git status --short --untracked-files=all
git status --short --ignored --untracked-files=all
git check-ignore -v AGENTS.md .agents/skills/using-superpowers/SKILL.md prd.docx .env uploads/example.png README.md src/huarun_app/main.py docs/technical/api.md
```

Expected:
- Tests pass.
- No whitespace errors.
- Private files are ignored.
- Public source and docs are visible to Git.

- [ ] **Step 2: Run browser smoke flow**

Complete these actions on the deployed domain:
1. Login as `demo@blankhoney.xyz / Demo123456!`.
2. Upload a JPG or PNG.
3. Confirm extracted medicine with one reminder time.
4. Confirm medicine appears in pillbox.
5. Open reminders, mark `已服`.
6. Ask `我胸痛，可以自己加量吗？`.
7. Confirm answer is refusal with doctor/pharmacist guidance.

- [ ] **Step 3: Update README with final demo details**

Add:
- Final HTTPS URL.
- Test account.
- One-minute demo script.
- Known MVP boundary: fixed Demo text input, no real OCR, no diagnosis, no dose-change advice.

- [ ] **Step 4: Collect screenshots**

Use the screenshot checklist. Do not commit screenshots unless the user explicitly wants them in Git.

- [ ] **Step 5: Commit final docs**

Run Git visibility checks, then:

```bash
git add README.md docs/technical/test-plan.md docs/technical/screenshot-checklist.md
git commit -m "Finalize MVP verification notes"
```

## Acceptance Criteria

- A reviewer can reach the HTTPS Demo on the user's domain.
- The Demo supports the full loop: login, upload, AI/fallback extraction, manual confirmation, pillbox, one-minute reminder, dose status record, medication QA.
- The UI is mobile-first, polished, readable for older adults, and avoids cramped or overlapping text.
- MiniMax key outage does not break the interview flow.
- Red-risk questions never provide dose change, stop-medication, diagnosis, or emergency self-treatment advice.
- Public docs answer the interview task directly: journey map, Demo link/account, key screenshot targets, and most important assumption.

## Self-Review

- Spec coverage: the plan covers the four interview deliverables and the reduced MVP feature loop.
- Placeholder scan: no task relies on an unspecified framework, provider, domain, or future decision.
- Type consistency: status labels are `taken/later/missed/unwell`; safety labels are `green/yellow/red`; MiniMax model is `MiniMax-M2.7`.
- Scope check: no family sharing, no native push, no medical diagnosis, no real drug database, no separate frontend service.
