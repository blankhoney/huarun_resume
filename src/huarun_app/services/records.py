from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo


STATUSES = ("taken", "later", "missed", "unwell")
DEFAULT_TIMEZONE = ZoneInfo("Asia/Shanghai")


def _record_value(record: Any, key: str) -> Any:
    if isinstance(record, dict):
        return record[key]
    return getattr(record, key)


def _as_timezone(value: datetime, target_timezone: ZoneInfo) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).astimezone(target_timezone)
    return value.astimezone(target_timezone)


def summarize_records(
    records: list[Any],
    *,
    now: datetime | None = None,
    days: int = 7,
    target_timezone: ZoneInfo = DEFAULT_TIMEZONE,
) -> dict[str, object]:
    current = _as_timezone(now or datetime.now(timezone.utc), target_timezone)
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
        planned_at = _as_timezone(_record_value(record, "planned_at"), target_timezone)
        status = _record_value(record, "status")
        if status not in totals:
            continue
        record_date = planned_at.date()
        if record_date not in day_rows:
            continue
        day_rows[record_date][status] += 1
        totals[status] += 1

    return {"totals": totals, "days": list(day_rows.values())}
