PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02"
    b"\xfeA\xe2&\xb5\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_demo_api_flow(client):
    login = client.post(
        "/api/auth/demo-login",
        json={"email": "demo@blankhoney.xyz", "password": "Demo123456!"},
    )
    assert login.status_code == 200

    scan = client.post(
        "/api/medicines/scan",
        files={"image": ("medicine.png", PNG_BYTES, "image/png")},
    )
    assert scan.status_code == 200
    scan_payload = scan.json()
    assert scan_payload["scan_id"]
    assert scan_payload["extraction"]["drug_name"]
    assert scan_payload["extraction"]["fallback_used"] is True

    scan_id = scan_payload["scan_id"]
    extraction = scan_payload["extraction"]

    rejected = client.post(
        f"/api/medicines/{scan_id}/confirm",
        json={
            "drug_name": extraction["drug_name"],
            "generic_name": extraction["generic_name"],
            "specification": extraction["specification"],
            "dose_text": extraction["visible_dose_text"],
            "warning_text": "。".join(extraction["warnings"]),
            "source_quotes": extraction["source_quotes"],
            "reminder_times": ["08:00", "20:00"],
            "confirmed": False,
        },
    )
    assert rejected.status_code == 400

    confirmed = client.post(
        f"/api/medicines/{scan_id}/confirm",
        json={
            "drug_name": extraction["drug_name"],
            "generic_name": extraction["generic_name"],
            "specification": extraction["specification"],
            "dose_text": extraction["visible_dose_text"],
            "warning_text": "。".join(extraction["warnings"]),
            "source_quotes": extraction["source_quotes"],
            "reminder_times": ["08:00", "20:00"],
            "confirmed": True,
        },
    )
    assert confirmed.status_code == 200
    medicine_id = confirmed.json()["medicine_id"]
    schedule_id = confirmed.json()["schedule_ids"][0]

    pillbox = client.get("/api/pillbox")
    assert pillbox.status_code == 200
    assert pillbox.json()["medicines"][0]["medicine_id"] == medicine_id

    reminders = client.get("/api/reminders/today")
    assert reminders.status_code == 200
    assert reminders.json()["reminders"]

    record = client.post(
        "/api/dose-records",
        json={"schedule_id": schedule_id, "status": "taken", "note": ""},
    )
    assert record.status_code == 200
    assert record.json()["status"] == "taken"

    summary = client.get("/api/records/summary?days=7")
    assert summary.status_code == 200
    assert summary.json()["totals"]["taken"] == 1

    red_qa = client.post(
        "/api/qa",
        json={"medicine_id": medicine_id, "question": "我胸痛，可以自己加量吗？"},
    )
    assert red_qa.status_code == 200
    assert red_qa.json()["safety_label"] == "red"

    green_qa = client.post(
        "/api/qa",
        json={"medicine_id": medicine_id, "question": "包装上写的一天几次？"},
    )
    assert green_qa.status_code == 200
    assert green_qa.json()["safety_label"] == "green"
    assert green_qa.json()["sources"]


def test_api_validation_errors_return_422(client):
    login = client.post(
        "/api/auth/demo-login",
        json={"email": "demo@blankhoney.xyz", "password": "Demo123456!"},
    )
    assert login.status_code == 200

    invalid_record = client.post(
        "/api/dose-records",
        json={"schedule_id": 999, "status": "unknown", "note": ""},
    )
    assert invalid_record.status_code == 422

    invalid_qa = client.post("/api/qa", json={"question": "短"})
    assert invalid_qa.status_code == 422
