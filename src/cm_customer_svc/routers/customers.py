import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from cm_customer_svc.models.customer import Customer
from cm_customer_svc.models.user import User
from cm_customer_svc.schemas.customer import CustomerCreate, CustomerUpdate
from cm_customer_svc.models.base import get_db
from cm_customer_svc.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

customers_router = APIRouter()


def _customer_to_dict(cust: Customer) -> dict:
    return {
        "customer_id": str(cust.customer_id),
        "customer_name": cust.customer_name,
        "customer_contact": cust.customer_contact,
        "customer_address": cust.customer_address,
        "managed_by": cust.managed_by,
        "created_at": cust.created_at.isoformat() if cust.created_at is not None else None,
        "updated_at": cust.updated_at.isoformat() if cust.updated_at is not None else None,
    }


def _parse_customer_pk(customer_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(customer_id))
    except (ValueError, TypeError) as e:
        logger.error(e, exc_info=True)
        # Treat invalid UUIDs as not found to avoid leaking implementation details
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer not found")


@customers_router.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db), _=Depends(get_current_user)) -> JSONResponse:
    """Create a new customer. Validate managed_by exists."""
    try:
        # validate managed_by exists
        manager = db.get(User, payload.managed_by)
        if manager is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"managed_by employee_id {payload.managed_by} does not exist")

        customer = Customer(
            customer_name=payload.customer_name,
            customer_contact=payload.customer_contact,
            customer_address=payload.customer_address,
            managed_by=payload.managed_by,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "customer created", "customer": _customer_to_dict(customer)})

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
def get_customer(customer_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)) -> JSONResponse:
    try:
        pk = _parse_customer_pk(customer_id)
        customer = db.get(Customer, pk)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer not found")
        return JSONResponse(status_code=status.HTTP_200_OK, content={"customer": _customer_to_dict(customer)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal server error")


@customers_router.put("/customers/{customer_id}")
def update_customer(customer_id: str, payload: CustomerUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)) -> JSONResponse:
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

        return JSONResponse(status_code=status.HTTP_200_OK, content={"customer": _customer_to_dict(customer)})

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
