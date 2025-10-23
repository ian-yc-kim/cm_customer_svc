from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.sql import func

from .base import Base


class User(Base):
    __tablename__ = "users"

    employee_id = Column(String(8), primary_key=True, unique=True, nullable=False)
    employee_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (Index("idx_user_employee_id", "employee_id"),)

    def __repr__(self) -> str:
        return f"<User(employee_id={self.employee_id}, employee_name={self.employee_name})>"
