from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from app.business.domain.value_objects import SalaryBasis, WageType

from .value_objects import PayrollPeriod


class PayrollRunStatus(StrEnum):
    DRAFT = "draft"
    COMMITTED = "committed"


@dataclass
class PayrollLineItem:
    id: UUID
    payroll_run_id: UUID
    employee_id: UUID

    employee_name: str
    wage_type: WageType
    wage_rate: Decimal
    working_hours_per_day: Decimal
    overtime_multiplier: Decimal
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


@dataclass
class PayrollRun:
    id: UUID
    business_id: UUID
    period: PayrollPeriod
    status: PayrollRunStatus
    is_incomplete: bool
    created_at: datetime
    updated_at: datetime
    line_items: list[PayrollLineItem] = field(default_factory=list)
