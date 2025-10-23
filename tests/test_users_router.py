from jose import jwt
from datetime import datetime, timedelta, timezone

from cm_customer_svc.routers.auth import ACCESS_TOKEN_COOKIE_NAME
from cm_customer_svc.config import SECRET_KEY, ALGORITHM


def test_me_success_with_valid_cookie(client):
    # login sets cookie
    resp = client.post("/api/auth/login", json={"username": "testuser", "password": "password"})
    assert resp.status_code == 200

    resp2 = client.get("/api/users/me")
    assert resp2.status_code == 200
    assert resp2.json().get("current_user_id") == "testuser"


def test_me_unauthorized_without_cookie(client):
    resp = client.get("/api/users/me")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Not authenticated"


def test_me_invalid_token_cookie(client):
    client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, "badtoken")
    resp = client.get("/api/users/me")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Invalid or expired token"


def test_me_expired_token_cookie(client):
    now = datetime.now(tz=timezone.utc)
    exp = now - timedelta(minutes=1)
    payload = {"sub": "expired_user", "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, token)
    resp = client.get("/api/users/me")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Invalid or expired token"
