from huarun_app.schemas import MedicineExtraction


DEMO_EMAIL = "demo@blankhoney.xyz"
DEMO_PASSWORD = "Demo123456!"
DEMO_MEDICINE_TEXT = (
    "药品名称：布洛芬缓释胶囊。规格：0.3g*20粒。用法用量：成人一次1粒，"
    "一日2次，早晚服用。本品可能引起胃部不适、恶心、头晕。对本品过敏者禁用，"
    "严重不适请咨询医生或药师。"
)
DEMO_EXTRACTION = MedicineExtraction(
    drug_name="布洛芬缓释胶囊",
    generic_name="布洛芬",
    specification="0.3g*20粒",
    visible_dose_text="成人一次1粒，一日2次，早晚服用",
    frequency_suggestion="每日 08:00, 20:00",
    warnings=["可能引起胃部不适、恶心、头晕", "对本品过敏者禁用"],
    source_quotes=["药品名称：布洛芬缓释胶囊", "用法用量：成人一次1粒，一日2次"],
    confidence=0.86,
    needs_manual_confirmation=True,
    fallback_used=True,
)
