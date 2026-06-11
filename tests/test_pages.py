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
