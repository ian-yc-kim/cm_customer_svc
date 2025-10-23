import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from cm_customer_svc.models.customer import Customer
from cm_customer_svc.models.user import User
from cm_customer_svc.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from cm_customer_svc.models.base import get_db
from cm_customer_svc.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

customers_router = APIRouter()


def _parse_customer_pk(customer_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(customer_id))
    except (ValueError, TypeError) as e:
        logger.error(e, exc_info=True)
        # Treat invalid UUIDs as not found to avoid leaking implementation details
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer not found")


@customers_router.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)) -> CustomerResponse:
    """Create a new customer. managed_by is set from authenticated user."""
    try:
        # validate current_user_id exists
        manager = db.get(User, current_user_id)
        if manager is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"managed_by employee_id {current_user_id} does not exist")

        customer = Customer(
            customer_name=payload.customer_name,
            customer_contact=payload.customer_contact,
            customer_address=payload.customer_address,
            managed_by=current_user_id,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        return CustomerResponse.model_validate(customer)

    except HTTPException:
        raise
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            logger.error("rollback failed", exc_info=True)
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal server error")


@customers_router.get("/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)) -> CustomerResponse:
    try:
        pk = _parse_customer_pk(customer_id)
        customer = db.get(Customer, pk)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer not found")
        return CustomerResponse.model_validate(customer)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal server error")


@customers_router.put("/customers/{customer_id}")
def update_customer(customer_id: str, payload: CustomerUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)) -> CustomerResponse:
    try:
        pk = _parse_customer_pk(customer_id)
        customer = db.get(Customer, pk)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer not found")

        # If managed_by present, validate existence
        if payload.managed_by is not None:
            manager = db.get(User, payload.managed_by)
            if manager is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"managed_by employee_id {payload.managed_by} does not exist")
            customer.managed_by = payload.managed_by

        # Update other optional fields
        if payload.customer_name is not None:
            customer.customer_name = payload.customer_name
        if payload.customer_contact is not None:
            customer.customer_contact = payload.customer_contact
        if payload.customer_address is not None:
            customer.customer_address = payload.customer_address

        db.add(customer)
        db.commit()
        db.refresh(customer)

        return CustomerResponse.model_validate(customer)

    except HTTPException:
        raise
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            logger.error("rollback failed", exc_info=True)
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal server error")


@customers_router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)) -> Response:
    try:
        pk = _parse_customer_pk(customer_id)
        customer = db.get(Customer, pk)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer not found")

        db.delete(customer)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            logger.error("rollback failed", exc_info=True)
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal server error")
