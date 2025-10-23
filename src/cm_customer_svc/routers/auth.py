import logging
from fastapi import APIRouter, Response, status, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from cm_customer_svc.utils.jwt_utils import create_access_token
from cm_customer_svc.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECURE_COOKIE,
    HTTP_ONLY_COOKIE,
    SAMESITE_COOKIE,
)
from cm_customer_svc.schemas.user import UserLogin
from cm_customer_svc.utils.password_utils import verify_password
from cm_customer_svc.models.base import get_db
from cm_customer_svc.models.user import User


logger = logging.getLogger(__name__)

auth_router = APIRouter()
ACCESS_TOKEN_COOKIE_NAME = "access_token"


@auth_router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user by employee_id and password, set access token cookie on success.

    Returns 401 on invalid credentials or internal failures during lookup/verification.
    """
    try:
        stmt = select(User).filter_by(employee_id=payload.employee_id)
        user = db.execute(stmt).scalar_one_or_none()
    except Exception as e:
        logger.error(e, exc_info=True)
        # Avoid leaking details; treat as invalid credentials
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, content='{"detail":"Invalid credentials"}', media_type="application/json")

    if not user:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, content='{"detail":"Invalid credentials"}', media_type="application/json")

    try:
        if not verify_password(payload.password, user.password_hash):
            return Response(status_code=status.HTTP_401_UNAUTHORIZED, content='{"detail":"Invalid credentials"}', media_type="application/json")
    except Exception as e:
        logger.error(e, exc_info=True)
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, content='{"detail":"Invalid credentials"}', media_type="application/json")

    try:
        token = create_access_token({"sub": user.employee_id})
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
    except Exception as e:
        logger.error(e, exc_info=True)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content='{"detail":"internal server error"}', media_type="application/json")


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
