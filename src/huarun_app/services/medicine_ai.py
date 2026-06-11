import json
import re
from typing import Any

from pydantic import ValidationError

from huarun_app.demo_data import DEMO_EXTRACTION
from huarun_app.schemas import MedicineExtraction, QaModelAnswer, SafetyLabel
from huarun_app.services.ai_client import complete_chat
from huarun_app.services.safety import classify_question


SYSTEM_PROMPT = (
    "你是“AI 用药伴侣”的药品信息整理助手。只能抽取和解释用户上传包装、"
    "说明书或系统提供文本中的信息。不得编造药名、剂量、频次、疗程、禁忌或适应症。"
    "不得建议用户自行加量、减量、停药、换药或合并用药。涉及胸痛、呼吸困难、"
    "严重过敏、意识障碍等高风险问题时，必须建议立即联系医生、药师或急救。"
    "输出必须是 JSON。"
)


def clean_model_text(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = cleaned.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def fallback_extraction() -> MedicineExtraction:
    return DEMO_EXTRACTION.model_copy(deep=True)


def extract_medicine_info(raw_text: str) -> MedicineExtraction:
    if not raw_text.strip():
        return fallback_extraction()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "请从以下药品包装或说明书文本中抽取 JSON，字段为 drug_name, "
                "generic_name, specification, visible_dose_text, frequency_suggestion, "
                "warnings, source_quotes, confidence, needs_manual_confirmation, fallback_used。"
                f"\n\n文本：{raw_text}"
            ),
        },
    ]

    try:
        content = clean_model_text(complete_chat(messages))
        payload = json.loads(content)
        result = MedicineExtraction.model_validate(payload)
        if not result.drug_name:
            return fallback_extraction()
        return result
    except (RuntimeError, json.JSONDecodeError, ValidationError, KeyError, TypeError):
        return fallback_extraction()


def refusal_answer(question: str) -> dict[str, Any]:
    return {
        "answer": (
            "这个问题涉及可能改变用药方案或高风险症状，我不能给出自行处理建议。"
            "请立即联系医生、药师；如出现胸痛、呼吸困难或严重过敏，请及时急救。"
        ),
        "sources": [],
        "safety_label": "red",
        "question": question,
    }


def _source_quotes_from_context(medicine_context: str) -> list[str]:
    parts = re.split(r"[。；;\n]", medicine_context)
    quotes = [part.strip() for part in parts if part.strip()]
    if not quotes:
        return ["当前 Demo 未提供可核验来源片段"]
    return quotes[:3]


def source_fallback_answer(
    question: str,
    medicine_context: str,
    safety_label: SafetyLabel,
) -> dict[str, Any]:
    sources = _source_quotes_from_context(medicine_context)
    guidance = "如症状持续或你不确定是否适合继续服用，请咨询医生或药师。"
    answer = (
        "根据当前说明书来源片段，我只能解释已提供的信息，不能补充未出现的剂量或疗程。"
        f"{guidance}"
    )
    if safety_label == "green":
        answer = (
            "根据当前说明书来源片段，请以包装或说明书写明的用法用量为准。"
            f"{guidance}"
        )
    return {
        "answer": answer,
        "sources": sources,
        "safety_label": safety_label,
        "question": question,
    }


def answer_medicine_question(question: str, medicine_context: str) -> dict[str, Any]:
    safety_label = classify_question(question)
    if safety_label == "red":
        return refusal_answer(question)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "请只基于给定药品文本回答用户问题，返回 JSON："
                '{"answer": "...", "sources": ["..."]}。'
                f"\n\n药品文本：{medicine_context}\n\n问题：{question}"
            ),
        },
    ]

    try:
        content = clean_model_text(complete_chat(messages))
        payload = json.loads(content)
        model_answer = QaModelAnswer.model_validate(payload)
        answer = model_answer.answer.strip()
        sources = [source.strip() for source in model_answer.sources if source.strip()][:3]
        if not sources:
            sources = _source_quotes_from_context(medicine_context)
        if not answer:
            raise ValueError("empty answer")
        return {
            "answer": answer,
            "sources": sources,
            "safety_label": safety_label,
            "question": question,
        }
    except (RuntimeError, json.JSONDecodeError, ValidationError, TypeError, ValueError):
        return source_fallback_answer(question, medicine_context, safety_label)
