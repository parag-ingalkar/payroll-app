from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.business.domain.value_objects import SalaryBasis, WageType
from app.payroll.domain.entities import PayrollRunStatus


# ──────────────── Request schemas ────────────────


class RunPayrollRequest(BaseModel):
    year: int
    month: int
    employee_ids: list[UUID] | None = None


# ──────────────── Response schemas ───────────────


class PayrollPeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start_date: date
    end_date: date


class PayrollLineItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    employee_name: str
    wage_type: WageType
    salary_basis: SalaryBasis

    basis_days: int
    total_days_in_period: int
    paid_days: Decimal
    lop_days: Decimal
    weekly_off_days: int
    holiday_days: int
    overtime_hours: Decimal

    per_day_rate: Decimal
    per_hour_rate: Decimal
    base_pay: Decimal
    overtime_pay: Decimal
    gross_pay: Decimal


class PayrollRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    period: PayrollPeriodRead
    status: PayrollRunStatus
    is_incomplete: bool
    created_at: datetime
    updated_at: datetime
    line_items: list[PayrollLineItemRead]


class PayrollRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    period: PayrollPeriodRead
    status: PayrollRunStatus
    is_incomplete: bool
    created_at: datetime
    updated_at: datetime
    total_gross_pay: Decimal
    employee_count: int
