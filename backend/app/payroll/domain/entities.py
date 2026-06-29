from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal

from app.payroll.domain.value_objects import (
    MissingAttendanceWarning,
    PayrollPeriod,
    PayrollStatus,
    AdjustmentType,
)
from app.payroll.domain.exceptions import InvalidStateTransitionError


@dataclass(slots=True)
class PayrollAdjustment:
    payroll_id: UUID
    employee_id: UUID
    adjustment_type: AdjustmentType
    amount: Decimal
    notes: str | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class PayrollLineItem:
    payroll_run_id: UUID
    employee_id: UUID
    employee_name: str
    designation: str | None

    present_days: Decimal
    half_days: Decimal
    paid_leave_days: Decimal
    unpaid_leave_days: Decimal
    paid_holiday_days: Decimal
    unpaid_holiday_days: Decimal

    overtime_hours: Decimal
    total_worked_hours: Decimal

    basic_pay: Decimal
    overtime_pay: Decimal
    gross_pay: Decimal

    adjustments_bonus: Decimal
    adjustments_deduction: Decimal

    net_pay: Decimal

    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class PayrollRun:
    business_id: UUID
    payroll_period: PayrollPeriod
    status: PayrollStatus

    created_at: datetime
    approved_at: datetime | None = None

    line_items: list[PayrollLineItem] = field(default_factory=list)
    adjustments: list[PayrollAdjustment] = field(default_factory=list)
    warnings: list[MissingAttendanceWarning] = field(default_factory=list)

    id: UUID = field(default_factory=uuid4)

    def is_draft(self) -> bool:
        return self.status == PayrollStatus.DRAFT

    def approve(self) -> None:
        if self.status != PayrollStatus.DRAFT:
            raise InvalidStateTransitionError(
                "Only draft payroll runs can be approved."
            )

        self.status = PayrollStatus.APPROVED
        self.approved_at = datetime.now()

    def add_line_item(self, line_item: PayrollLineItem) -> None:
        if self.status != PayrollStatus.DRAFT:
            raise InvalidStateTransitionError(
                "Cannot add line items to a non-draft payroll run."
            )

        self.line_items.append(line_item)

    def replace_line_items(self, new_line_items: list[PayrollLineItem]) -> None:
        if self.status != PayrollStatus.DRAFT:
            raise InvalidStateTransitionError(
                "Cannot replace line items in a non-draft payroll run."
            )

        self.line_items = new_line_items

    def total_net_pay(self) -> Decimal:
        return sum((item.net_pay for item in self.line_items), start=Decimal(0.00))
    
    def add_warning(self, warning: MissingAttendanceWarning) -> None:
        self.warnings.append(warning)

    def add_adjustments(self, adjustments: list[PayrollAdjustment]) -> None:
        if self.status != PayrollStatus.DRAFT:
            raise InvalidStateTransitionError(
                "Cannot add adjustments to a non-draft payroll run."
            )

        self.adjustments.extend(adjustments)