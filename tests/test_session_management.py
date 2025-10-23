import pytest
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from cm_customer_svc.utils.jwt_utils import create_access_token, decode_access_token
from cm_customer_svc.routers.auth import ACCESS_TOKEN_COOKIE_NAME
from cm_customer_svc.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, SECURE_COOKIE


# Unit tests for jwt_utils
def test_create_access_token_structure_and_claims():
    token = create_access_token({"sub": "unit_user"})
    # verify signature and payload using jose directly
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert payload.get("sub") == "unit_user"
    assert "iat" in payload
    assert "exp" in payload
    # exp should be after iat
    assert int(payload["exp"]) > int(payload["iat"])


def test_decode_access_token_valid_token():
    token = create_access_token({"sub": "valid_user"})
    data = decode_access_token(token)
    assert data.get("sub") == "valid_user"


def test_decode_access_token_invalid_signature_raises():
    token = create_access_token({"sub": "sig_user"})
    # tamper signature segment
    parts = token.split(".")
    if len(parts) == 3:
        parts[2] = "A" * len(parts[2])
    tampered = ".".join(parts)
    with pytest.raises(JWTError):
        decode_access_token(tampered)


def test_decode_access_token_expired_token_raises():
    now = datetime.now(tz=timezone.utc)
    exp = now - timedelta(minutes=5)
    payload = {"iat": int(now.timestamp()), "exp": int(exp.timestamp()), "sub": "expired_unit"}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(JWTError):
        decode_access_token(token)


def test_decode_access_token_missing_claims_returns_payload_without_sub():
    # create token that intentionally lacks 'sub'
    now = datetime.now(tz=timezone.utc)
    exp = now + timedelta(minutes=5)
    payload = {"iat": int(now.timestamp()), "exp": int(exp.timestamp()), "custom": "value"}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    data = decode_access_token(token)
    # decode should succeed but 'sub' is absent
    assert "sub" not in data
    assert data.get("custom") == "value"


# Integration tests using TestClient fixture
def test_login_success_sets_secure_http_only_cookie(client):
    resp = client.post("/api/auth/login", json={"username": "testuser", "password": "password"})
    assert resp.status_code == 200

    sc = resp.headers.get("set-cookie", "")
    assert "access_token=" in sc
    # HttpOnly present
    assert "httponly" in sc.lower()
    # SameSite present (Lax expected)
    assert "samesite=lax" in sc.lower()
    # max-age presence for 24h default in config (ACCESS_TOKEN_EXPIRE_MINUTES)
    expected_max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert str(expected_max_age) in sc
    # secure flag when configured
    if SECURE_COOKIE:
        assert "secure" in sc.lower()


def test_login_failure_bad_credentials_returns_401(client):
    resp = client.post("/api/auth/login", json={"username": "testuser", "password": "badpass"})
    assert resp.status_code == 401


def test_logout_clears_session_cookie(client):
    # perform logout
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    sc = resp.headers.get("set-cookie", "")
    assert "access_token=" in sc
    # cookie cleared via max-age=0
    assert "max-age=0" in sc.lower() or "max-age=0" in sc


def test_users_me_with_valid_session_cookie(client):
    # login to obtain cookie stored in TestClient
    resp = client.post("/api/auth/login", json={"username": "testuser", "password": "password"})
    assert resp.status_code == 200

    # subsequent request should include cookie automatically
    resp2 = client.get("/api/users/me")
    assert resp2.status_code == 200
    assert resp2.json().get("current_user_id") == "testuser"


def test_users_me_without_cookie_returns_401(client):
    # ensure no cookie present by clearing client cookies
    client.cookies.clear()
    resp = client.get("/api/users/me")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Not authenticated"


def test_users_me_with_invalid_session_cookie_returns_401(client):
    client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, "this-is-not-a-valid-token")
    resp = client.get("/api/users/me")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Invalid or expired token"


def test_users_me_with_expired_session_cookie_returns_401(client):
    now = datetime.now(tz=timezone.utc)
    exp = now - timedelta(minutes=10)
    payload = {"iat": int(now.timestamp()), "exp": int(exp.timestamp()), "sub": "expired_integration"}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, token)
    resp = client.get("/api/users/me")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Invalid or expired token"
