from pydantic import ValidationError

from huarun_app.settings import get_settings
from huarun_app.schemas import ConfirmMedicinePayload, MedicineExtraction
from huarun_app.services import ai_client
from huarun_app.services.medicine_ai import (
    answer_medicine_question,
    clean_model_text,
    fallback_extraction,
    refusal_answer,
)


def test_medicine_extraction_defaults_to_manual_confirmation():
    result = MedicineExtraction(
        drug_name="布洛芬缓释胶囊",
        generic_name="布洛芬",
        specification="0.3g*20粒",
        visible_dose_text="成人一次1粒，一日2次",
        frequency_suggestion="每日 08:00, 20:00",
        warnings=["胃部不适者慎用"],
        source_quotes=["药品名称：布洛芬缓释胶囊"],
        confidence=0.82,
    )

    assert result.needs_manual_confirmation is True
    assert result.fallback_used is False
    assert result.confidence == 0.82


def test_medicine_extraction_rejects_invalid_confidence():
    try:
        MedicineExtraction(
            drug_name="布洛芬缓释胶囊",
            confidence=1.5,
        )
    except ValidationError as exc:
        assert "confidence" in str(exc)
    else:
        raise AssertionError("invalid confidence should fail validation")


def test_confirm_payload_requires_human_confirmation():
    try:
        ConfirmMedicinePayload(
            scan_id=1,
            drug_name="布洛芬缓释胶囊",
            visible_dose_text="成人一次1粒，一日2次",
            reminder_times=["08:00", "20:00"],
            confirmed=False,
        )
    except ValidationError as exc:
        assert "confirmed" in str(exc)
    else:
        raise AssertionError("unconfirmed medicine should fail validation")


def test_clean_model_text_removes_think_tags():
    text = '<think>internal</think>{"drug_name":"布洛芬"}'

    assert clean_model_text(text) == '{"drug_name":"布洛芬"}'


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


def test_configured_minimax_failure_is_wrapped(monkeypatch):
    class BrokenCompletions:
        def create(self, **_kwargs):
            raise ValueError("network down")

    class BrokenClient:
        def __init__(self, **_kwargs):
            self.chat = type("Chat", (), {"completions": BrokenCompletions()})()

    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(ai_client, "OpenAI", BrokenClient)

    try:
        ai_client.complete_chat([{"role": "user", "content": "hello"}])
    except RuntimeError as exc:
        assert "MiniMax request failed" in str(exc)
    else:
        raise AssertionError("MiniMax client failures should be wrapped")
    finally:
        get_settings.cache_clear()
