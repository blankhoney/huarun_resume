from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import sessionmaker

from huarun_app.database import build_engine
from huarun_app.models import Base, User
from huarun_app.services.records import summarize_records


def test_summarize_records_counts_last_seven_days():
    now = datetime(2026, 6, 12, 8, 0, tzinfo=timezone.utc)
    records = [
        {"planned_at": now, "status": "taken"},
        {"planned_at": now - timedelta(days=1), "status": "missed"},
        {"planned_at": now - timedelta(days=1), "status": "unwell"},
        {"planned_at": now - timedelta(days=8), "status": "taken"},
    ]

    summary = summarize_records(records, now=now, days=7)

    assert summary["totals"] == {"taken": 1, "later": 0, "missed": 1, "unwell": 1}
    assert len(summary["days"]) == 7
    assert summary["days"][-1]["date"] == "2026-06-12"


def test_summarize_records_uses_shanghai_date_boundary():
    now = datetime(2026, 6, 11, 17, 0, tzinfo=timezone.utc)

    summary = summarize_records([{"planned_at": now, "status": "taken"}], now=now, days=1)

    assert summary["days"][0]["date"] == "2026-06-12"
    assert summary["days"][0]["taken"] == 1


def test_sqlite_memory_database_creates_user_table():
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        user = User(
            email="demo@example.com",
            password_hash="demo",
            name="Demo User",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id == 1
