# app/business/presentation/schemas.py
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.business.domain.entities import WageType, Weekday
from app.business.domain.value_objects import normalize_whitespace


class BusinessWeeklyOffRuleBase(BaseModel):
    weekday: Weekday
    week_of_month: int | None = Field(default=None, ge=1, le=5)


class BusinessWeeklyOffRuleCreate(BusinessWeeklyOffRuleBase):
    pass


class BusinessWeeklyOffRuleRead(BusinessWeeklyOffRuleBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class BusinessBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    default_wage_type: WageType
    default_working_hours_per_day: Decimal = Field(
        gt=0,
        le=24,
        max_digits=5,
        decimal_places=2,
    )
    default_overtime_multiplier: Decimal = Field(
        ge=1,
        max_digits=5,
        decimal_places=2,
    )
    payroll_start_day: int = Field(default=1, ge=1, le=28)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = normalize_whitespace(value)
        if not normalized:
            raise ValueError("Business name must not be empty.")
        return normalized


class BusinessCreate(BusinessBase):
    weekly_off_rules: list[BusinessWeeklyOffRuleCreate] = Field(default_factory=list)


class BusinessUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    default_wage_type: WageType | None = None
    default_working_hours_per_day: Decimal | None = Field(
        default=None,
        gt=0,
        le=24,
        max_digits=5,
        decimal_places=2,
    )
    default_overtime_multiplier: Decimal | None = Field(
        default=None,
        ge=1,
        max_digits=5,
        decimal_places=2,
    )
    payroll_start_day: int | None = Field(default=None, ge=1, le=28)

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_whitespace(value)
        if not normalized:
            raise ValueError("Business name must not be empty.")
        return normalized


class BusinessRead(BaseModel):
    id: UUID
    owner_id: str
    name: str
    default_wage_type: WageType
    default_working_hours_per_day: Decimal
    default_overtime_multiplier: Decimal
    payroll_start_day: int
    weekly_off_rules: list[BusinessWeeklyOffRuleRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
