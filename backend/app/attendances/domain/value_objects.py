from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True, frozen=True)
class AttendanceSummary:
    employee_id: UUID

    period_start_date: date
    period_end_date: date

    attendance_days: set[date]

    present_days: Decimal
    half_days: Decimal
    paid_leave_days: Decimal
    unpaid_leave_days: Decimal
    paid_holiday_days: Decimal
    unpaid_holiday_days: Decimal

    overtime_hours: Decimal
    total_worked_hours: Decimal