def test_records_summary_days_must_be_between_one_and_thirty(client):
    login = client.post(
        "/api/auth/demo-login",
        json={"email": "demo@blankhoney.xyz", "password": "Demo123456!"},
    )
    assert login.status_code == 200

    too_small = client.get("/api/records/summary?days=0")
    too_large = client.get("/api/records/summary?days=31")
    accepted = client.get("/api/records/summary?days=30")

    assert too_small.status_code == 422
    assert too_large.status_code == 422
    assert accepted.status_code == 200
