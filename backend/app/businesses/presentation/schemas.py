from pydantic import BaseModel, ConfigDict, Field
from app.shared.value_objects import Weekday, WageType, SalaryBasis
from decimal import Decimal
from uuid import UUID


class WeeklyOffRuleBase(BaseModel):
    weekday: Weekday


class WeeklyOffRuleCreate(WeeklyOffRuleBase):
    pass


class BusinessBase(BaseModel):
    name: str = Field(..., max_length=255)
    default_wage_type: WageType
    default_working_hours_per_day: Decimal = Field(..., gt=0, le=24)
    default_overtime_multiplier: Decimal = Field(..., ge=1)
    default_salary_basis: SalaryBasis
    payroll_start_day: int = Field(..., ge=1, le=28)


class BusinessCreate(BusinessBase):
    weekly_off_rules: list[WeeklyOffRuleCreate] = Field(default_factory=list)


class BusinessUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    default_wage_type: WageType | None = None
    default_working_hours_per_day: Decimal | None = Field(None, gt=0, le=24)
    default_overtime_multiplier: Decimal | None = Field(None, ge=1)
    default_salary_basis: SalaryBasis | None = None
    payroll_start_day: int | None = Field(None, ge=1, le=28)


class WeeklyOffRuleResponse(WeeklyOffRuleBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class BusinessResponse(BusinessBase):
    id: UUID
    owner_id: str
    slug: str
    weekly_off_rules: list[WeeklyOffRuleResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
