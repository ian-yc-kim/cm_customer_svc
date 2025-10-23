from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
import re

from cm_customer_svc.utils.validation_utils import (
    sanitize_input,
    validate_phone_number_format,
    validate_employee_id_format,
)


class CustomerCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=100)
    customer_contact: Optional[str] = None
    customer_address: Optional[str] = None

    @field_validator("customer_name", mode="before")
    @classmethod
    def _sanitize_name(cls, v: Any) -> str:
        return sanitize_input(v)

    @field_validator("customer_contact", mode="before", check_fields=False)
    @classmethod
    def _validate_contact(cls, v: Any) -> Optional[str]:
        return validate_phone_number_format(v)

    @field_validator("customer_address", mode="before", check_fields=False)
    @classmethod
    def _sanitize_address(cls, v: Any) -> Optional[str]:
        return sanitize_input(v)


class CustomerResponse(BaseModel):
    customer_id: UUID
    customer_name: str
    customer_contact: Optional[str]
    customer_address: Optional[str]
    managed_by: str
    created_at: datetime
    updated_at: datetime

    # allow building from ORM-like objects (SQLAlchemy instances)
    model_config = ConfigDict(from_attributes=True)


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    customer_address: Optional[str] = None
    managed_by: Optional[str] = None

    @field_validator("customer_name", mode="before", check_fields=False)
    @classmethod
    def _sanitize_name(cls, v: Any) -> Optional[str]:
        return sanitize_input(v)

    @field_validator("customer_contact", mode="before", check_fields=False)
    @classmethod
    def _validate_contact(cls, v: Any) -> Optional[str]:
        return validate_phone_number_format(v)

    @field_validator("customer_address", mode="before", check_fields=False)
    @classmethod
    def _sanitize_address(cls, v: Any) -> Optional[str]:
        return sanitize_input(v)

    @field_validator("managed_by", mode="before", check_fields=False)
    @classmethod
    def _validate_managed_by(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        try:
            return validate_employee_id_format(v)
        except Exception:
            if isinstance(v, str) and re.fullmatch(r"EMP\d{5}", v):
                return v
            raise
