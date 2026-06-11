from datetime import datetime, timedelta, timezone
from typing import Any


STATUSES = ("taken", "later", "missed", "unwell")


def _record_value(record: Any, key: str) -> Any:
    if isinstance(record, dict):
        return record[key]
    return getattr(record, key)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def summarize_records(
    records: list[Any],
    *,
    now: datetime | None = None,
    days: int = 7,
) -> dict[str, object]:
    current = _as_utc(now or datetime.now(timezone.utc))
    start_date = current.date() - timedelta(days=days - 1)
    day_rows = {
        start_date + timedelta(days=offset): {
            "date": (start_date + timedelta(days=offset)).isoformat(),
            "taken": 0,
            "later": 0,
            "missed": 0,
            "unwell": 0,
        }
        for offset in range(days)
    }
    totals = {status: 0 for status in STATUSES}

    for record in records:
        planned_at = _as_utc(_record_value(record, "planned_at"))
        status = _record_value(record, "status")
        if status not in totals:
            continue
        record_date = planned_at.date()
        if record_date not in day_rows:
            continue
        day_rows[record_date][status] += 1
        totals[status] += 1

    return {"totals": totals, "days": list(day_rows.values())}
