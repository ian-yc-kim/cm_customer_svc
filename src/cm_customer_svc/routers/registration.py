import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from cm_customer_svc.schemas.user import UserCreate
from cm_customer_svc.models.user import User
from cm_customer_svc.models.base import get_db
from cm_customer_svc.utils.password_utils import hash_password

logger = logging.getLogger(__name__)

registration_router = APIRouter()


@registration_router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> JSONResponse:
    """Register a new user: validate, hash password, persist to DB.

    Returns 201 on success. On duplicate employee_id returns 409.
    """
    try:
        # Hash the incoming password
        hashed = hash_password(payload.password)

        user = User(
            employee_id=payload.employee_id,
            employee_name=payload.employee_name,
            password_hash=hashed,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": "user created", "employee_id": user.employee_id},
        )

    except IntegrityError as e:
        # Likely duplicate primary key / unique constraint
        try:
            db.rollback()
        except Exception:
            logger.error("rollback failed", exc_info=True)
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="employee_id already exists")

    except Exception as e:
        try:
            db.rollback()
        except Exception:
            logger.error("rollback failed", exc_info=True)
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal server error")
