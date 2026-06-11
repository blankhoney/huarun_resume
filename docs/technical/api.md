# 接口设计

## 通用约定

- 所有接口使用 `/api` 前缀。
- Demo 使用 session cookie 鉴权，不设计复杂权限系统。
- API 路由实现集中在 `src/huarun_app/main.py`，页面路由在 `src/huarun_app/routers/pages.py`。
- 时间使用 ISO 8601 字符串；提醒时间使用 `HH:MM`。
- 失败响应包含 `detail` 字段。
- 未人工确认的药品不能进入药箱和提醒。

## 数据类型

| 类型 | 字段 |
| --- | --- |
| `MedicineExtraction` | `drug_name`, `generic_name`, `specification`, `visible_dose_text`, `frequency_suggestion`, `warnings`, `source_quotes`, `confidence`, `needs_manual_confirmation`, `fallback_used` |
| `DoseStatus` | `taken`, `later`, `missed`, `unwell` |
| `SafetyLabel` | `green`, `yellow`, `red` |

## POST /api/auth/demo-login

用途：使用固定测试账号进入 Demo。

请求：`email`, `password`。

成功响应：返回用户信息，并写入 session cookie。

失败：账号或密码错误返回 401。

## POST /api/medicines/scan

用途：上传药品包装图片，触发 OCR 或 Demo 文本兜底，并返回 AI 结构化结果。

请求：`multipart/form-data`，字段 `image`，仅支持 JPG 和 PNG。

成功响应字段：`scan_id`, `image_url`, `raw_text`, `extraction`。

失败：
- 非图片格式返回 400。
- 未登录返回 401。
- 模型失败不返回 500，而是返回 `fallback_used=true` 的识别结果。

示例请求：

```bash
curl -X POST http://127.0.0.1:8000/api/medicines/scan \
  -b cookie.txt \
  -F "image=@sample-medicine.png;type=image/png"
```

示例响应：

```json
{
  "scan_id": 12,
  "image_url": "/uploads/12/sample-medicine.png",
  "raw_text": "药品名称：布洛芬缓释胶囊。规格：0.3g*20粒。用法用量：成人一次1粒，一日2次，早晚服用。",
  "extraction": {
    "drug_name": "布洛芬缓释胶囊",
    "generic_name": "布洛芬",
    "specification": "0.3g*20粒",
    "visible_dose_text": "成人一次1粒，一日2次，早晚服用",
    "frequency_suggestion": "每日 08:00, 20:00",
    "warnings": ["可能引起胃部不适、恶心、头晕", "对本品过敏者禁用"],
    "source_quotes": ["药品名称：布洛芬缓释胶囊", "用法用量：成人一次1粒，一日2次"],
    "confidence": 0.86,
    "needs_manual_confirmation": true,
    "fallback_used": true
  }
}
```

## POST /api/medicines/{scan_id}/confirm

用途：保存人工确认后的药品信息和提醒时间。

请求字段：`drug_name`, `generic_name`, `specification`, `dose_text`, `warning_text`, `reminder_times`, `confirmed`。

成功响应字段：`medicine_id`, `schedule_ids`。

失败：
- `confirmed=false` 返回 400。
- 找不到 scan 返回 404。
- 未登录返回 401。

示例请求：

```json
{
  "drug_name": "布洛芬缓释胶囊",
  "generic_name": "布洛芬",
  "specification": "0.3g*20粒",
  "dose_text": "成人一次1粒，一日2次，早晚服用",
  "warning_text": "可能引起胃部不适、恶心、头晕。严重不适请咨询医生或药师。",
  "reminder_times": ["08:00", "20:00"],
  "confirmed": true
}
```

示例响应：

```json
{
  "medicine_id": 7,
  "schedule_ids": [21, 22]
}
```

## GET /api/pillbox

用途：获取当前 Demo 用户的电子药箱卡片。

成功响应：药品列表，每项包含 `medicine_id`, `drug_name`, `specification`, `dose_text`, `reminder_times`, `today_status`, `image_url`。

## GET /api/reminders/today

用途：获取今日提醒。MVP 允许生成 1 分钟 Demo 提醒，便于面试演示。

成功响应：提醒列表，每项包含 `schedule_id`, `medicine_id`, `drug_name`, `planned_at`, `status`。

## POST /api/dose-records

用途：记录一次服药状态。

请求字段：`schedule_id`, `status`, `note`。

成功响应字段：`record_id`, `status`, `recorded_at`。

失败：
- `status` 不在 `taken/later/missed/unwell` 返回 422。
- 找不到 schedule 返回 404。

示例请求：

```json
{
  "schedule_id": 21,
  "status": "taken",
  "note": ""
}
```

示例响应：

```json
{
  "record_id": 31,
  "status": "taken",
  "recorded_at": "2026-06-12T08:02:11+08:00"
}
```

## POST /api/qa

用途：围绕当前药品做用药知识问答。

请求字段：`medicine_id`, `question`。

成功响应字段：`answer`, `sources`, `safety_label`。

安全规则：
- 红色问题直接拒答，不调用模型。
- 黄色问题提示不能替代医生或药师。
- 绿色问题基于药品文本回答并显示来源。
- MiniMax key 为空、网络失败或返回不可解析内容时，绿色和黄色问题返回基于 `source_quotes` 的保守兜底回答。

示例请求：

```json
{
  "medicine_id": 7,
  "question": "包装上写的一天几次？"
}
```

示例响应：

```json
{
  "answer": "根据已确认的包装文字，这个药的可见用法是成人一次1粒，一日2次，早晚服用。请以医生医嘱或说明书为准。",
  "sources": ["用法用量：成人一次1粒，一日2次"],
  "safety_label": "green"
}
```

红色问题示例：

```json
{
  "medicine_id": 7,
  "question": "我胸痛，可以自己加量吗？"
}
```

红色响应示例：

```json
{
  "answer": "这个问题涉及胸痛和自行调整剂量，我不能提供加量、停药或诊断建议。请尽快联系医生或药师；如果胸痛明显、持续或伴随呼吸困难，请及时就医或呼叫急救。",
  "sources": [],
  "safety_label": "red"
}
```

## GET /api/records/summary?days=7

用途：获取近 7 天服药记录摘要。

成功响应字段：`totals`, `days`。`totals` 汇总四种状态，`days` 按日期列出每天状态数量。

## 接口验收顺序

1. 登录。
2. 上传图片并获得 `scan_id`。
3. 确认药品并获得 `medicine_id`。
4. 查询药箱。
5. 查询今日提醒。
6. 记录 `taken`。
7. 查询 7 天摘要。
8. 提交红色问答并确认拒答。
