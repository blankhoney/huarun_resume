from sqlalchemy import inspect

from huarun_app.database import build_engine
from huarun_app.models import Base
from tests.test_api_flow import PNG_BYTES


def _login(client):
    response = client.post(
        "/api/auth/demo-login",
        json={"email": "demo@blankhoney.xyz", "password": "Demo123456!"},
    )
    assert response.status_code == 200


def _scan_payload(client):
    _login(client)
    scan = client.post(
        "/api/medicines/scan",
        files={"image": ("medicine.png", PNG_BYTES, "image/png")},
    )
    assert scan.status_code == 200
    payload = scan.json()
    extraction = payload["extraction"]
    return payload["scan_id"], {
        "drug_name": extraction["drug_name"],
        "generic_name": extraction["generic_name"],
        "specification": extraction["specification"],
        "dose_text": extraction["visible_dose_text"],
        "warning_text": "。".join(extraction["warnings"]),
        "source_quotes": extraction["source_quotes"],
        "reminder_times": ["08:00", "20:00"],
        "confirmed": True,
    }


def _confirmed_schedule(client):
    scan_id, body = _scan_payload(client)
    confirmed = client.post(f"/api/medicines/{scan_id}/confirm", json=body)
    assert confirmed.status_code == 200
    return confirmed.json()["schedule_ids"][0]


def test_confirming_same_scan_twice_returns_existing_medicine(client):
    scan_id, body = _scan_payload(client)
    body["reminder_times"] = ["20:00", "08:00"]

    first = client.post(f"/api/medicines/{scan_id}/confirm", json=body)
    second = client.post(f"/api/medicines/{scan_id}/confirm", json=body)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()

    pillbox = client.get("/api/pillbox")
    assert pillbox.status_code == 200
    assert len(pillbox.json()["medicines"]) == 1

    reminders = client.get("/api/reminders/today")
    assert reminders.status_code == 200
    assert len(reminders.json()["reminders"]) == 2


def test_recording_same_schedule_updates_existing_record(client):
    schedule_id = _confirmed_schedule(client)

    first = client.post(
        "/api/dose-records",
        json={"schedule_id": schedule_id, "status": "taken", "note": ""},
    )
    second = client.post(
        "/api/dose-records",
        json={"schedule_id": schedule_id, "status": "taken", "note": "same day"},
    )
    changed = client.post(
        "/api/dose-records",
        json={"schedule_id": schedule_id, "status": "missed", "note": "changed"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert changed.status_code == 200
    assert second.json()["record_id"] == first.json()["record_id"]
    assert changed.json()["record_id"] == first.json()["record_id"]
    assert changed.json()["status"] == "missed"

    summary = client.get("/api/records/summary?days=7")
    assert summary.status_code == 200
    assert summary.json()["totals"]["taken"] == 0
    assert summary.json()["totals"]["missed"] == 1


def test_idempotent_resources_have_database_unique_constraints():
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)

    medicine_constraints = {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("medicines")
    }
    dose_constraints = {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("dose_records")
    }

    assert ("scan_id",) in medicine_constraints
    assert ("schedule_id", "planned_at") in dose_constraints
