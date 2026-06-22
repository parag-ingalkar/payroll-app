from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.business.domain.value_objects import SalaryBasis, WageType


class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    designation: str | None = Field(default=None, max_length=255)
    wage_type: WageType | None = None
    salary_basis: SalaryBasis | None = None
    wage_rate: Decimal = Field(..., gt=0)
    working_hours_per_day: Decimal | None = Field(default=None, gt=0)
    overtime_multiplier: Decimal | None = Field(default=None, gt=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Employee name cannot be empty.")
        return stripped

    @field_validator("designation")
    @classmethod
    def strip_designation(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        return stripped or None


class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    designation: str | None = None
    wage_type: WageType | None = None
    salary_basis: SalaryBasis | None = None
    wage_rate: Decimal | None = Field(default=None, gt=0)
    working_hours_per_day: Decimal | None = Field(default=None, gt=0)
    overtime_multiplier: Decimal | None = Field(default=None, gt=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("Employee name cannot be empty.")
        return stripped

    @field_validator("designation")
    @classmethod
    def strip_designation(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        return stripped or None


class EmployeeRead(BaseModel):
    id: UUID
    business_id: UUID
    name: str
    designation: str | None
    wage_type: WageType
    wage_rate: Decimal
    salary_basis: SalaryBasis
    working_hours_per_day: Decimal
    overtime_multiplier: Decimal
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
