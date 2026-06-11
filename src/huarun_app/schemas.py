from typing import Literal

from pydantic import BaseModel, Field


DoseStatus = Literal["taken", "later", "missed", "unwell"]
SafetyLabel = Literal["green", "yellow", "red"]


class MedicineExtraction(BaseModel):
    drug_name: str = Field(..., min_length=1)
    generic_name: str = ""
    specification: str = ""
    visible_dose_text: str = ""
    frequency_suggestion: str = ""
    warnings: list[str] = Field(default_factory=list)
    source_quotes: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    needs_manual_confirmation: bool = True
    fallback_used: bool = False


class ConfirmMedicinePayload(BaseModel):
    scan_id: int = Field(..., gt=0)
    drug_name: str = Field(..., min_length=1)
    generic_name: str = ""
    specification: str = ""
    visible_dose_text: str = Field(..., min_length=1)
    reminder_times: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_quotes: list[str] = Field(default_factory=list)
    confirmed: Literal[True]


class DoseRecordPayload(BaseModel):
    schedule_id: int = Field(..., gt=0)
    status: DoseStatus
    note: str = ""


class QaPayload(BaseModel):
    question: str = Field(..., min_length=2, max_length=300)
    medicine_id: int | None = Field(default=None, gt=0)
