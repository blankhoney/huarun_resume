import json
import re
from io import BytesIO
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from huarun_app.database import get_db, init_db
from huarun_app.demo_data import DEMO_MEDICINE_TEXT
from huarun_app.models import (
    DoseRecord,
    Medicine,
    MedicineScan,
    QaLog,
    ReminderSchedule,
    User,
)
from huarun_app.routers.pages import router as page_router
from huarun_app.schemas import ConfirmMedicinePayload, DoseRecordPayload, QaPayload
from huarun_app.services.medicine_ai import (
    answer_medicine_question,
    extract_medicine_info,
)
from huarun_app.services.records import summarize_records
from huarun_app.settings import get_settings, validate_production_settings


IMAGE_FORMAT_EXTENSIONS = {"JPEG": "jpg", "PNG": "png"}
IMAGE_MEDIA_TYPES = {"jpg": "image/jpeg", "png": "image/png"}


def create_app() -> FastAPI:
    settings = get_settings()
    validate_production_settings(settings)
    init_db()
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="AI 用药伴侣 MVP")
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        https_only=settings.app_env.lower() == "production",
    )
    app.mount(
        "/assets",
        StaticFiles(directory="assets", check_dir=False),
        name="assets",
    )
    app.include_router(page_router)

    @app.post("/api/auth/demo-login")
    async def demo_login(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
        payload = await request.json()
        return _demo_login_from_payload(request, db, payload)

    @app.post("/api/medicines/scan")
    async def scan_medicine(
        request: Request,
        image: UploadFile = File(...),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        user = _require_user(request, db)
        image_bytes = await image.read()
        if len(image_bytes) > settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="Image is larger than 5MB")

        extension = _validated_image_extension(image_bytes)
        filename = f"{int(datetime.now().timestamp())}-{uuid4().hex}.{extension}"
        user_dir = upload_path / str(user.id)
        user_dir.mkdir(parents=True, exist_ok=True)
        image_path = user_dir / filename
        image_path.write_bytes(image_bytes)

        raw_text = DEMO_MEDICINE_TEXT
        extraction = extract_medicine_info(raw_text)
        scan = MedicineScan(
            user_id=user.id,
            image_path=str(image_path.relative_to(upload_path)),
            raw_text=raw_text,
            extraction_json=extraction.model_dump_json(),
            fallback_used=extraction.fallback_used,
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        return {
            "scan_id": scan.id,
            "image_url": f"/uploads/{scan.image_path}",
            "raw_text": raw_text,
            "extraction": extraction.model_dump(),
        }

    @app.get("/uploads/{user_id}/{filename}")
    def uploaded_image(
        user_id: int,
        filename: str,
        request: Request,
        db: Session = Depends(get_db),
    ) -> FileResponse:
        user = _require_user(request, db)
        if user.id != user_id:
            raise HTTPException(status_code=404, detail="Image not found")

        if Path(filename).name != filename:
            raise HTTPException(status_code=404, detail="Image not found")

        extension = filename.rsplit(".", maxsplit=1)[-1].lower()
        media_type = IMAGE_MEDIA_TYPES.get(extension)
        if media_type is None:
            raise HTTPException(status_code=404, detail="Image not found")

        user_dir = (upload_path / str(user.id)).resolve()
        image_path = (user_dir / filename).resolve()
        if image_path.parent != user_dir or not image_path.is_file():
            raise HTTPException(status_code=404, detail="Image not found")

        return FileResponse(image_path, media_type=media_type)

    @app.post("/api/medicines/{scan_id}/confirm")
    async def confirm_medicine(
        scan_id: int,
        request: Request,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        user = _require_user(request, db)
        body = await request.json()
        if body.get("confirmed") is not True:
            raise HTTPException(status_code=400, detail="Human confirmation is required")

        payload = _normalize_confirm_payload(scan_id, body)
        scan = db.get(MedicineScan, scan_id)
        if scan is None or scan.user_id != user.id:
            raise HTTPException(status_code=404, detail="Scan not found")

        existing_medicine = db.scalar(
            select(Medicine).where(Medicine.user_id == user.id, Medicine.scan_id == scan.id)
        )
        if existing_medicine is not None:
            schedules = db.scalars(
                select(ReminderSchedule)
                .where(ReminderSchedule.medicine_id == existing_medicine.id)
                .order_by(ReminderSchedule.id)
            ).all()
            return {
                "medicine_id": existing_medicine.id,
                "schedule_ids": [schedule.id for schedule in schedules],
            }

        warning_text = body.get("warning_text") or "。".join(payload.warnings)
        medicine = Medicine(
            user_id=user.id,
            scan_id=scan.id,
            drug_name=payload.drug_name,
            generic_name=payload.generic_name,
            specification=payload.specification,
            dose_text=payload.visible_dose_text,
            warning_text=warning_text,
            source_quotes_json=json.dumps(payload.source_quotes, ensure_ascii=False),
            confidence=_scan_confidence(scan),
        )
        db.add(medicine)
        db.flush()

        times = payload.reminder_times or ["08:00", "20:00"]
        schedules = [
            ReminderSchedule(medicine_id=medicine.id, time_of_day=_safe_time(value))
            for value in times
        ]
        db.add_all(schedules)
        db.commit()

        return {
            "medicine_id": medicine.id,
            "schedule_ids": [schedule.id for schedule in schedules],
        }

    @app.get("/api/pillbox")
    def pillbox(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
        user = _require_user(request, db)
        medicines = db.scalars(
            select(Medicine).where(Medicine.user_id == user.id).order_by(Medicine.id)
        ).all()
        return {"medicines": [_medicine_card(medicine) for medicine in medicines]}

    @app.get("/api/reminders/today")
    def today_reminders(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
        user = _require_user(request, db)
        schedules = db.scalars(
            select(ReminderSchedule)
            .join(Medicine)
            .where(Medicine.user_id == user.id, ReminderSchedule.active.is_(True))
            .order_by(ReminderSchedule.time_of_day)
        ).all()
        return {"reminders": [_reminder_item(schedule, db) for schedule in schedules]}

    @app.post("/api/dose-records")
    async def create_dose_record(
        request: Request,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        user = _require_user(request, db)
        payload = _validate_payload(DoseRecordPayload, await request.json())
        schedule = db.get(ReminderSchedule, payload.schedule_id)
        if schedule is None or schedule.medicine.user_id != user.id:
            raise HTTPException(status_code=404, detail="Schedule not found")

        planned_at = _planned_at_today(schedule.time_of_day)
        record = db.scalar(
            select(DoseRecord).where(
                DoseRecord.schedule_id == schedule.id,
                DoseRecord.planned_at == planned_at,
            )
        )
        if record is None:
            record = DoseRecord(
                schedule_id=schedule.id,
                planned_at=planned_at,
                status=payload.status,
                note=payload.note,
            )
            db.add(record)
        else:
            record.status = payload.status
            record.note = payload.note
            record.recorded_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
        return {
            "record_id": record.id,
            "status": record.status,
            "recorded_at": record.recorded_at.isoformat(),
        }

    @app.post("/api/qa")
    async def qa(
        request: Request,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        user = _require_user(request, db)
        payload = _validate_payload(QaPayload, await request.json())
        medicine = None
        if payload.medicine_id is not None:
            medicine = db.get(Medicine, payload.medicine_id)
            if medicine is None or medicine.user_id != user.id:
                raise HTTPException(status_code=404, detail="Medicine not found")

        context = _medicine_context(medicine)
        answer = answer_medicine_question(payload.question, context)
        qa_log = QaLog(
            user_id=user.id,
            medicine_id=medicine.id if medicine else None,
            question=payload.question,
            answer=answer["answer"],
            safety_label=answer["safety_label"],
            source_quotes_json=json.dumps(answer["sources"], ensure_ascii=False),
        )
        db.add(qa_log)
        db.commit()
        return {
            "answer": answer["answer"],
            "sources": answer["sources"],
            "safety_label": answer["safety_label"],
        }

    @app.get("/api/records/summary")
    def records_summary(
        request: Request,
        days: int = Query(default=7, ge=1, le=30),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        user = _require_user(request, db)
        records = db.scalars(
            select(DoseRecord)
            .join(ReminderSchedule)
            .join(Medicine)
            .where(Medicine.user_id == user.id)
        ).all()
        return summarize_records(list(records), days=days)

    return app


def _demo_login_from_payload(
    request: Request,
    db: Session,
    payload: dict[str, Any],
) -> dict[str, Any]:
    settings = get_settings()
    if (
        payload.get("email") != settings.demo_email
        or payload.get("password") != settings.demo_password
    ):
        raise HTTPException(status_code=401, detail="Invalid demo account")

    user = db.scalar(select(User).where(User.email == settings.demo_email))
    if user is None:
        user = User(
            email=settings.demo_email,
            password_hash=settings.demo_password,
            name="Demo User",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    request.session["user_id"] = user.id
    return {"user": {"id": user.id, "email": user.email, "name": user.name}}


def _require_user(request: Request, db: Session) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Login required")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Login required")
    return user


def _normalize_confirm_payload(
    scan_id: int,
    body: dict[str, Any],
) -> ConfirmMedicinePayload:
    payload = {
        **body,
        "scan_id": scan_id,
        "visible_dose_text": body.get("visible_dose_text") or body.get("dose_text") or "",
    }
    if "warnings" not in payload:
        warning_text = body.get("warning_text", "")
        payload["warnings"] = [item for item in re.split(r"[。；;\n]", warning_text) if item]
    return _validate_payload(ConfirmMedicinePayload, payload)


def _validate_payload(model: type[BaseModel], payload: dict[str, Any]) -> Any:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=_validation_detail(exc)) from exc


def _validation_detail(exc: ValidationError) -> list[dict[str, Any]]:
    return [
        {
            "loc": list(error.get("loc", ())),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        for error in exc.errors(include_url=False)
    ]


def _scan_confidence(scan: MedicineScan) -> float:
    try:
        return float(json.loads(scan.extraction_json).get("confidence", 0.0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0.0


def _validated_image_extension(image_bytes: bytes) -> str:
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            image_format = img.format
            img.verify()
    except (SyntaxError, UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=415,
            detail="Only valid JPG and PNG images are supported",
        ) from exc

    extension = IMAGE_FORMAT_EXTENSIONS.get(image_format or "")
    if extension is None:
        raise HTTPException(
            status_code=415,
            detail="Only valid JPG and PNG images are supported",
        )
    return extension


def _safe_time(value: str) -> str:
    try:
        return time.fromisoformat(value).strftime("%H:%M")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid reminder time: {value}") from exc


def _planned_at_today(time_of_day: str) -> datetime:
    app_timezone = ZoneInfo(get_settings().app_timezone)
    planned_time = time.fromisoformat(time_of_day)
    local_planned_at = datetime.combine(
        datetime.now(app_timezone).date(),
        planned_time,
        tzinfo=app_timezone,
    )
    return local_planned_at.astimezone(timezone.utc)


def _reminder_item(schedule: ReminderSchedule, db: Session) -> dict[str, Any]:
    planned_at = _planned_at_today(schedule.time_of_day)
    record = db.scalar(
        select(DoseRecord)
        .where(DoseRecord.schedule_id == schedule.id)
        .order_by(DoseRecord.recorded_at.desc())
    )
    return {
        "schedule_id": schedule.id,
        "medicine_id": schedule.medicine_id,
        "drug_name": schedule.medicine.drug_name,
        "time_of_day": schedule.time_of_day,
        "planned_at": planned_at.isoformat(),
        "status": record.status if record else "pending",
    }


def _medicine_card(medicine: Medicine) -> dict[str, Any]:
    return {
        "medicine_id": medicine.id,
        "drug_name": medicine.drug_name,
        "generic_name": medicine.generic_name,
        "specification": medicine.specification,
        "dose_text": medicine.dose_text,
        "warning_text": medicine.warning_text,
        "reminder_times": [schedule.time_of_day for schedule in medicine.schedules],
        "today_status": "pending",
        "image_url": f"/uploads/{medicine.scan.image_path}" if medicine.scan else "",
    }


def _medicine_context(medicine: Medicine | None) -> str:
    if medicine is None:
        return ""
    sources = []
    try:
        sources = json.loads(medicine.source_quotes_json)
    except json.JSONDecodeError:
        sources = []
    parts = [
        f"药品名称：{medicine.drug_name}",
        f"规格：{medicine.specification}",
        f"用法用量：{medicine.dose_text}",
        medicine.warning_text,
        *sources,
    ]
    return "。".join(part for part in parts if part)


app = create_app()
