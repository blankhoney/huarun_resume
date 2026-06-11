from tests.test_api_flow import PNG_BYTES


def test_login_and_home_pages_render(client):
    login_page = client.get("/login")
    assert login_page.status_code == 200
    assert "AI 用药伴侣" in login_page.text

    client.post(
        "/api/auth/demo-login",
        json={"email": "demo@blankhoney.xyz", "password": "Demo123456!"},
    )
    home_page = client.get("/")
    assert home_page.status_code == 200
    assert "拍照添加药品" in home_page.text
    assert "今日提醒" in home_page.text
    assert "问一问" in home_page.text


def test_qa_page_defaults_to_first_medicine(client):
    client.post(
        "/api/auth/demo-login",
        json={"email": "demo@blankhoney.xyz", "password": "Demo123456!"},
    )
    scan = client.post(
        "/api/medicines/scan",
        files={"image": ("medicine.png", PNG_BYTES, "image/png")},
    )
    extraction = scan.json()["extraction"]
    confirmed = client.post(
        f"/api/medicines/{scan.json()['scan_id']}/confirm",
        json={
            "drug_name": extraction["drug_name"],
            "generic_name": extraction["generic_name"],
            "specification": extraction["specification"],
            "dose_text": extraction["visible_dose_text"],
            "warning_text": "。".join(extraction["warnings"]),
            "source_quotes": extraction["source_quotes"],
            "reminder_times": ["08:00"],
            "confirmed": True,
        },
    )
    medicine_id = confirmed.json()["medicine_id"]

    page = client.get("/qa")

    assert page.status_code == 200
    assert f'<option value="{medicine_id}" selected>' in page.text
