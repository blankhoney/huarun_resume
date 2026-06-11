from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120), default="Demo User")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    scans: Mapped[list["MedicineScan"]] = relationship(back_populates="user")
    medicines: Mapped[list["Medicine"]] = relationship(back_populates="user")


class MedicineScan(Base):
    __tablename__ = "medicine_scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    image_path: Mapped[str] = mapped_column(String(500), default="")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    extraction_json: Mapped[str] = mapped_column(Text, default="{}")
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    user: Mapped[User] = relationship(back_populates="scans")
    medicine: Mapped["Medicine | None"] = relationship(
        back_populates="scan",
        uselist=False,
    )


class Medicine(Base):
    __tablename__ = "medicines"
    __table_args__ = (UniqueConstraint("scan_id", name="uq_medicines_scan_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    scan_id: Mapped[int | None] = mapped_column(ForeignKey("medicine_scans.id"))
    drug_name: Mapped[str] = mapped_column(String(255))
    generic_name: Mapped[str] = mapped_column(String(255), default="")
    specification: Mapped[str] = mapped_column(String(255), default="")
    dose_text: Mapped[str] = mapped_column(Text, default="")
    warning_text: Mapped[str] = mapped_column(Text, default="")
    source_quotes_json: Mapped[str] = mapped_column(Text, default="[]")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    user: Mapped[User] = relationship(back_populates="medicines")
    scan: Mapped[MedicineScan | None] = relationship(back_populates="medicine")
    schedules: Mapped[list["ReminderSchedule"]] = relationship(
        back_populates="medicine",
        cascade="all, delete-orphan",
    )


class ReminderSchedule(Base):
    __tablename__ = "reminder_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id"))
    time_of_day: Mapped[str] = mapped_column(String(5))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    medicine: Mapped[Medicine] = relationship(back_populates="schedules")
    records: Mapped[list["DoseRecord"]] = relationship(back_populates="schedule")


class DoseRecord(Base):
    __tablename__ = "dose_records"
    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            "planned_at",
            name="uq_dose_records_schedule_planned_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("reminder_schedules.id"))
    planned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    note: Mapped[str] = mapped_column(Text, default="")

    schedule: Mapped[ReminderSchedule] = relationship(back_populates="records")


class QaLog(Base):
    __tablename__ = "qa_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    medicine_id: Mapped[int | None] = mapped_column(ForeignKey("medicines.id"))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    safety_label: Mapped[str] = mapped_column(String(20))
    source_quotes_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
