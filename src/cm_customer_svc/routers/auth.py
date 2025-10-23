from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from typing import Dict

from cm_customer_svc.utils.jwt_utils import create_access_token
from cm_customer_svc.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECURE_COOKIE,
    HTTP_ONLY_COOKIE,
    SAMESITE_COOKIE,
)

auth_router = APIRouter()
ACCESS_TOKEN_COOKIE_NAME = "access_token"


class UserLogin(BaseModel):
    username: str
    password: str


@auth_router.post("/login")
def login(payload: UserLogin):
    # Hardcoded authentication for this task
    if payload.username != "testuser" or payload.password != "password":
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, content='{"detail":"Invalid credentials"}', media_type="application/json")

    token = create_access_token({"sub": payload.username})
    max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60

    resp = Response(content='{"message": "login successful"}', media_type="application/json")
    resp.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=HTTP_ONLY_COOKIE,
        secure=SECURE_COOKIE,
        samesite=SAMESITE_COOKIE,
    )
    return resp


@auth_router.post("/logout")
def logout():
    # Clear cookie by setting empty value and max_age=0
    resp = Response(content='{"message": "logout successful"}', media_type="application/json")
    resp.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value="",
        max_age=0,
        httponly=HTTP_ONLY_COOKIE,
        secure=SECURE_COOKIE,
        samesite=SAMESITE_COOKIE,
    )
    return resp
