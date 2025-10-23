import pytest
from fastapi import Request, HTTPException
from jose import jwt
from datetime import datetime, timedelta, timezone

from cm_customer_svc.dependencies.auth import get_current_user
from cm_customer_svc.utils.jwt_utils import create_access_token
from cm_customer_svc.routers.auth import ACCESS_TOKEN_COOKIE_NAME
from cm_customer_svc.config import SECRET_KEY, ALGORITHM


def _make_scope(cookie: str | None = None) -> dict:
    headers = []
    if cookie is not None:
        headers.append((b"cookie", cookie.encode()))
    # minimal ASGI scope for Request construction
    return {"type": "http", "method": "GET", "path": "/", "headers": headers}


def test_get_current_user_success():
    token = create_access_token({"sub": "testuser"})
    scope = _make_scope(f"{ACCESS_TOKEN_COOKIE_NAME}={token}")
    req = Request(scope)

    user = get_current_user(req)
    assert user == "testuser"


def test_get_current_user_missing_cookie():
    scope = _make_scope()
    req = Request(scope)
    with pytest.raises(HTTPException) as exc:
        get_current_user(req)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Not authenticated"


def test_get_current_user_invalid_token():
    scope = _make_scope(f"{ACCESS_TOKEN_COOKIE_NAME}=not-a-token")
    req = Request(scope)
    with pytest.raises(HTTPException) as exc:
        get_current_user(req)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or expired token"


def test_get_current_user_expired_token():
    now = datetime.now(tz=timezone.utc)
    exp = now - timedelta(minutes=1)
    payload = {"sub": "expired_user", "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    scope = _make_scope(f"{ACCESS_TOKEN_COOKIE_NAME}={token}")
    req = Request(scope)
    with pytest.raises(HTTPException) as exc:
        get_current_user(req)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or expired token"
