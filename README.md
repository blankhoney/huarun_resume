# AI 用药伴侣 MVP

面向华润三九前置评估的可体验 Web/H5 Demo。它展示一个中老年用药管理闭环：上传药品包装、AI 整理可见信息、人工确认、进入电子药箱、记录今日提醒、进行用药问答，并对高风险问题直接拒答。

## 在线体验

- 地址：`https://huarun-demo.blankhoney.xyz/login`
- 账号：`demo@blankhoney.xyz`
- 密码：`HuarunDemo123456!`

登录页不会预填密码。输入上面的演示密码后进入首页。

## 演示流程

1. 登录 Demo 账号。
2. 点击“拍照添加药品”，上传 JPG/PNG 药品包装图。
3. 查看 AI 整理出的药品名称、规格、用法、警示信息、来源片段和置信度。
4. 勾选人工确认，保存到电子药箱。
5. 进入电子药箱查看药品卡片和提醒时间。
6. 进入今日提醒，标记“已服”“稍后”“漏服”或“不适”。
7. 进入问答页，分别测试普通问题和高风险问题，例如“我胸痛，可以自己加量吗？”。

## 项目定位

这个 MVP 不是完整医疗系统，也不替代医生或药师。它验证的是一个产品假设：AI 可以降低录入药品信息的成本，但药名、用法和提醒时间必须由用户人工确认后才进入管理流程。

当前上传接口会校验并保存真实 JPG/PNG 图片；为了保证测试题流程稳定可复现，识别输入使用内置药品说明文本。MiniMax 不可用、未配置或返回异常时，系统会进入固定 Demo 兜底结果。

更多产品说明见 [MVP 范围文档](docs/product/mvp-scope.md)。

## 技术栈

- FastAPI + Jinja2：单服务提供页面和 API。
- Vanilla JS：处理上传预览、登录、确认、提醒记录和问答交互。
- PostgreSQL：生产部署保存 Demo 用户、药品、提醒、服药记录和问答日志。
- SQLite：本地开发和测试默认可用。
- Pydantic：约束 AI 结构化结果、确认 payload、问答和状态枚举。
- MiniMax-M2.7：用于文本结构化和用药问答；图片 OCR/视觉识别不在当前 MVP 范围内。
- Docker Compose + Caddy：部署到 Debian 13 VPS，Caddy 自动 HTTPS。

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
uvicorn huarun_app.main:app --reload
```

访问：

```text
http://127.0.0.1:8000
```

本地默认账号：

```text
demo@blankhoney.xyz
Demo123456!
```

生产环境不能使用这个默认密码；`APP_ENV=production` 会拒绝默认值、过短密码和占位符。

## 环境变量

| 变量 | 示例 | 说明 |
| --- | --- | --- |
| `APP_ENV` | `production` | 生产部署开启安全配置校验 |
| `POSTGRES_PASSWORD` | `replace-with-strong-password` | Docker Compose 中 PostgreSQL 密码 |
| `DATABASE_URL` | `postgresql+psycopg://huarun:replace-with-strong-password@postgres:5432/huarun` | PostgreSQL 连接串 |
| `SESSION_SECRET` | `replace-with-32-plus-random-chars` | session cookie 签名密钥，生产环境不少于 32 字符 |
| `MINIMAX_BASE_URL` | `https://api.minimax.io/v1` | MiniMax OpenAI-compatible 地址 |
| `MINIMAX_API_KEY` | `sk-...` | MiniMax key，仅放在服务器 `.env` |
| `MINIMAX_MODEL` | `MiniMax-M2.7` | 文本结构化和问答模型 |
| `DEMO_EMAIL` | `demo@blankhoney.xyz` | 演示账号 |
| `DEMO_PASSWORD` | `HuarunDemo123456!` | 线上演示密码，生产必须显式设置 |
| `APP_TIMEZONE` | `Asia/Shanghai` | 提醒和 7 天摘要展示时区 |
| `DEMO_DOMAIN` | `huarun-demo.blankhoney.xyz` | Caddy 对外域名 |

## VPS 部署

目标服务器：

```text
Debian 13
43.130.244.175
huarun-demo.blankhoney.xyz
```

DNS 需要创建 `A` 记录：

```text
huarun-demo.blankhoney.xyz -> 43.130.244.175
```

不要把 `huarun_demo.blankhoney.xyz` 作为 Caddy 自动 HTTPS 域名使用。下划线不适合作为公开 Web 主机名，可能导致 TLS 证书签发失败。

服务器本地创建 `.env`，不要提交到 Git：

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
DEMO_PASSWORD=HuarunDemo123456!
APP_TIMEZONE=Asia/Shanghai
EOF
```

启动和检查：

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 app
curl -I https://huarun-demo.blankhoney.xyz/login
```

`POSTGRES_PASSWORD` 如果包含 `@`、`:`、`/` 等特殊字符，`DATABASE_URL` 里要使用 URL 编码。Caddy 会自动申请 HTTPS 证书。

## 测试

```bash
pytest -q
git diff --check
docker compose config
```

生产变量缺失时，`docker compose config` 应失败并提示缺少必需变量；显式提供生产变量时应通过。

## 关键目录

```text
src/huarun_app/        FastAPI 应用、模型、页面路由和业务服务
assets/                前端 CSS 和 Vanilla JS
tests/                 单元测试、API 流程测试和安全回归测试
docs/product/          产品介绍和 MVP 范围
docs/technical/        技术选型、接口、测试、截图和执行记录
docker-compose.yml     PostgreSQL、App、Caddy 编排
Caddyfile              HTTPS 反向代理配置
```

## 安全边界

- AI 不做诊断。
- AI 不建议自行加量、减量、停药、换药或合并用药。
- 红色风险问题本地规则拒答，不调用模型。
- 上传图片只接受真实 JPG/PNG，并要求登录后访问。
- `.env`、API key、session secret、本地数据库和上传文件不提交到 Git。
