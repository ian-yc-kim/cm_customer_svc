from pydantic import BaseModel, Field, field_validator
from typing import Any

from cm_customer_svc.utils.validation_utils import (
    validate_employee_id_format,
    sanitize_input,
    validate_password_strength,
)


class UserCreate(BaseModel):
    employee_id: str = Field(min_length=8, max_length=8)
    employee_name: str = Field(min_length=1, max_length=100)
    password: str

    @field_validator("employee_id", mode="before")
    @classmethod
    def _validate_employee_id(cls, v: Any) -> str:
        return validate_employee_id_format(v)

    @field_validator("employee_name", mode="before")
    @classmethod
    def _sanitize_name(cls, v: Any) -> str:
        return sanitize_input(v)

    @field_validator("password", mode="before")
    @classmethod
    def _validate_password(cls, v: Any) -> str:
        return validate_password_strength(v)


class UserLogin(BaseModel):
    employee_id: str = Field(min_length=8, max_length=8)
    password: str

    @field_validator("employee_id", mode="before")
    @classmethod
    def _validate_employee_id(cls, v: Any) -> str:
        return validate_employee_id_format(v)
