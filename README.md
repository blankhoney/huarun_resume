# AI 用药伴侣 MVP

面向华润三九前置评估的最小可体验 Demo。目标是在一个移动端优先的 Web/H5 页面里展示：上传药品图片、AI 整理信息、人工确认、电子药箱、1 分钟 Demo 提醒、服药状态记录、用药问答和高风险拒答。

## 项目目标

- 让面试评审可以通过 HTTPS Demo 地址完整体验核心闭环。
- 展示用户旅程地图、关键代码/配置截图和最需要验证的假设。
- 明确医疗安全边界：AI 不做诊断、不改剂量、不替代医生或药师。

## 技术选型

- FastAPI + Jinja2：单服务同时提供页面和 API。
- Vanilla JS：处理上传预览、表单提交、状态记录和问答渲染。
- PostgreSQL：保存 Demo 用户、药品、提醒、服药记录和问答日志。
- MiniMax-M2.7：用于文本结构化和用药问答；图片理解不强依赖模型视觉能力。
- Docker Compose + Caddy：部署到 Debian 13 VPS，Caddy 自动 HTTPS。

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
uvicorn huarun_app.main:app --reload
```

访问 `http://127.0.0.1:8000`。

## 环境变量

| 变量 | 示例 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://huarun:huarun@postgres:5432/huarun` | PostgreSQL 连接串 |
| `SESSION_SECRET` | `change-me` | session cookie 签名密钥 |
| `MINIMAX_BASE_URL` | `https://api.minimax.io/v1` | MiniMax OpenAI-compatible 地址 |
| `MINIMAX_API_KEY` | `sk-...` | MiniMax key，仅放在服务器 `.env` |
| `MINIMAX_MODEL` | `MiniMax-M2.7` | 文本结构化和问答模型 |
| `DEMO_EMAIL` | `demo@blankhoney.xyz` | 测试账号 |
| `DEMO_PASSWORD` | `Demo123456!` | 测试密码 |
| `DEMO_DOMAIN` | `your-domain.example` | Caddy 对外域名 |

## 测试账号

- 邮箱：`demo@blankhoney.xyz`
- 密码：`Demo123456!`

## VPS 部署

在 Debian 13 VPS 上安装 Docker 和 Docker Compose 后，创建服务器本地 `.env`：

```bash
cat > .env <<'EOF'
DEMO_DOMAIN=your-domain.example
DATABASE_URL=postgresql+psycopg://huarun:huarun@postgres:5432/huarun
SESSION_SECRET=replace-with-long-random-string
MINIMAX_BASE_URL=https://api.minimax.io/v1
MINIMAX_API_KEY=replace-on-server-only
MINIMAX_MODEL=MiniMax-M2.7
DEMO_EMAIL=demo@blankhoney.xyz
DEMO_PASSWORD=Demo123456!
EOF
docker compose up -d --build
docker compose logs -f app
```

## Demo 演示脚本

1. 使用测试账号登录。
2. 上传一张 JPG/PNG 药品包装图。
3. 查看识别字段、来源片段和置信度。
4. 勾选人工确认，保存提醒时间。
5. 在电子药箱查看药品卡片。
6. 进入今日提醒，标记“已服”或“不适”。
7. 在问答页分别提问普通问题和高风险问题。

## 面试截图清单

优先截图：首页、上传确认、电子药箱、提醒记录、问答拒答、System Prompt、AI 工作流、Pydantic Schema、FastAPI 路由、Docker Compose、Caddyfile。

## MVP 边界

- OCR 和 MiniMax 都是增强能力；任何失败都会进入固定 Demo 兜底流程。
- 红色风险问题本地拒答，不调用模型。
- 不做诊断、换药、加减剂量、家属分享、短信/微信提醒、医生后台或真实药品数据库。
