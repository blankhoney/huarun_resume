from fastapi.testclient import TestClient

from tests.test_api_flow import PNG_BYTES


def _login(client):
    response = client.post(
        "/api/auth/demo-login",
        json={"email": "demo@blankhoney.xyz", "password": "Demo123456!"},
    )
    assert response.status_code == 200


def test_rejects_spoofed_html_upload(client):
    _login(client)

    response = client.post(
        "/api/medicines/scan",
        files={"image": ("x.html", b"<script>alert(1)</script>", "image/png")},
    )

    assert response.status_code == 415


def test_rejects_corrupted_png_upload(client):
    corrupted_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
        b"\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02"
        b"\xfeA\xe2&\xb5\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    _login(client)

    response = client.post(
        "/api/medicines/scan",
        files={"image": ("corrupt.png", corrupted_png, "image/png")},
    )

    assert response.status_code == 415


def test_rejects_oversized_upload_before_image_parsing(client):
    _login(client)

    response = client.post(
        "/api/medicines/scan",
        files={"image": ("large.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")},
    )

    assert response.status_code == 413


def test_uploaded_image_requires_session_and_serves_image_type(client):
    _login(client)
    scan = client.post(
        "/api/medicines/scan",
        files={"image": ("medicine.html", PNG_BYTES, "text/html")},
    )
    assert scan.status_code == 200

    image_url = scan.json()["image_url"]
    assert image_url.startswith("/uploads/1/")
    assert image_url.endswith(".png")

    image = client.get(image_url)
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content == PNG_BYTES

    with TestClient(client.app) as unauthenticated:
        blocked = unauthenticated.get(image_url)

    assert blocked.status_code == 401


def test_uploaded_image_cannot_be_read_by_another_user(client, monkeypatch):
    from huarun_app.settings import get_settings

    _login(client)
    scan = client.post(
        "/api/medicines/scan",
        files={"image": ("medicine.png", PNG_BYTES, "image/png")},
    )
    assert scan.status_code == 200
    image_url = scan.json()["image_url"]

    monkeypatch.setenv("DEMO_EMAIL", "other@example.com")
    monkeypatch.setenv("DEMO_PASSWORD", "Other123456!")
    get_settings.cache_clear()
    try:
        other_login = client.post(
            "/api/auth/demo-login",
            json={"email": "other@example.com", "password": "Other123456!"},
        )
        assert other_login.status_code == 200

        blocked = client.get(image_url)
    finally:
        get_settings.cache_clear()

    assert blocked.status_code == 404
