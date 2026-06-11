from pydantic import ValidationError

from huarun_app.schemas import ConfirmMedicinePayload, MedicineExtraction


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
