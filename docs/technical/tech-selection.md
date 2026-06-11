# 技术框架选型

## 选型结论

MVP 使用 Python 优先的单体 Web 架构：FastAPI 提供页面和 API，Jinja2 负责服务端渲染，Vanilla JS 做少量交互，PostgreSQL 持久化数据，MiniMax-M2.7 做文本结构化和问答，Docker Compose + Caddy 部署到 Debian 13 VPS。

## 为什么不用前后端分离

前后端分离能展示更完整的工程分层，但对这个测试题来说会增加 Next.js 构建、API 联调、部署服务数量和截图范围。当前目标是 1-3 天内交付一个稳定、好看、可访问的面试 Demo，因此单体 FastAPI 更符合 MVP。

## 模块选型

| 模块 | 选型 | 原因 |
| --- | --- | --- |
| Web 框架 | FastAPI | Python 生态适合 AI 接入，自动 OpenAPI 文档适合展示接口能力 |
| 页面渲染 | Jinja2 | 不引入前端框架，减少构建和部署复杂度 |
| 前端交互 | Vanilla JS | 只需要上传预览、表单提交、状态记录和问答渲染 |
| 数据库 | PostgreSQL | 比 SQLite 更接近部署环境，也便于展示真实持久化设计 |
| ORM | SQLAlchemy 2 | 数据模型清晰，测试时可切换 SQLite 内存库 |
| AI 模型 | MiniMax-M2.7 | 用户已有包月套餐，用于结构化抽取和用药问答 |
| 图片识别 | 固定 Demo 文本输入 | 当前 MVP 不接真实 OCR，不假设 M2.7 具备稳定图片输入能力，保证演示可靠 |
| 部署 | Docker Compose | 单机 VPS 可复现，服务边界清楚 |
| HTTPS | Caddy | 自动 HTTPS 和反向代理配置简洁 |

## AI 工作流设计

上传图片后，系统校验并保存真实 JPG/PNG，但当前 MVP 使用内置 Demo 药品文本继续流程，不执行真实 OCR。MiniMax-M2.7 只负责把文本整理成固定字段，不能直接保存用药计划。结构化抽取失败时接口仍返回固定 Demo 结构化结果，并标记 `fallback_used=true`。

问答分两层处理：先用本地规则识别红色风险问题；红色问题直接拒答，不调用模型。绿色和黄色问题再结合当前药品文本交给 MiniMax-M2.7，回答必须带来源片段或“不确定，请咨询医生/药师”。如果 MiniMax key 为空、网络失败或返回不可解析内容，问答服务使用当前药品来源片段生成保守兜底回答，不中断 Demo 流程。

## 部署设计

VPS 上运行三个容器：`app`、`postgres`、`caddy`。`app` 暴露 8000 给内部网络，`caddy` 监听 80 和 443 并反向代理到 app。PostgreSQL 数据、上传目录和 Caddy 证书数据使用 Docker volume 持久化。

## 取舍

- 牺牲：不做复杂前端状态管理、不做原生通知、不接真实药品数据库、不做家属分享。
- 获得：实现路径短、演示稳定、部署简单、截图材料集中、医疗安全边界更容易讲清楚。
