import pytest
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from cm_customer_svc.utils.jwt_utils import create_access_token, decode_access_token
from cm_customer_svc.config import SECRET_KEY, ALGORITHM


def test_create_access_token_includes_sub_and_exp():
    token = create_access_token({"sub": "user123"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "user123"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_access_token_valid():
    token = create_access_token({"sub": "user456"})
    data = decode_access_token(token)
    assert data["sub"] == "user456"


def test_decode_access_token_expired_raises():
    now = datetime.now(tz=timezone.utc)
    exp = now - timedelta(minutes=1)
    payload = {"sub": "expired_user", "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(JWTError):
        decode_access_token(token)


def test_decode_access_token_invalid_signature_raises():
    token = create_access_token({"sub": "x"})
    # tamper signature portion
    parts = token.split(".")
    if len(parts) == 3:
        parts[2] = "a" * len(parts[2])
    tampered = ".".join(parts)
    with pytest.raises(JWTError):
        decode_access_token(tampered)
