from cm_customer_svc.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECURE_COOKIE


def test_login_sets_secure_http_only_cookie(client):
    resp = client.post("/api/auth/login", json={"username": "testuser", "password": "password"})
    assert resp.status_code == 200
    sc = resp.headers.get("set-cookie", "")
    assert "access_token=" in sc
    assert "httponly" in sc.lower()
    # max-age may be present; check presence
    expected_max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert str(expected_max_age) in sc
    assert "samesite=lax" in sc.lower()
    if SECURE_COOKIE:
        assert "secure" in sc.lower()


def test_logout_clears_cookie(client):
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    sc = resp.headers.get("set-cookie", "")
    assert "access_token=" in sc
    assert "max-age=0" in sc.lower() or "max-age=0" in sc
