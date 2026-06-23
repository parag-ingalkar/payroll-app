from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.attendance.domain.entities import Attendance, AttendanceStatus
from app.business.domain.entities import Business, WeeklyOffRule
from app.employees.domain.entities import Employee
from app.holidays.domain.entities import Holiday

from .value_objects import DayPayInfo, PayDayMap, PayDayType, PayrollPeriod


@dataclass
class EmployeePayrollContext:
    employee: Employee
    business: Business
    attendance_records: Sequence[Attendance]
    holidays: Sequence[Holiday]


def _is_weekly_off(d: date, rules: Sequence[WeeklyOffRule]) -> bool:
    """Return True if *d* is a weekly-off day according to the given rules."""
    day_name = d.strftime("%A").upper()  # e.g. "MONDAY"
    for rule in rules:
        if rule.weekday.upper() == day_name:
            return True
    return False


class DayClassifier:
    @staticmethod
    def classify_period(
        period: PayrollPeriod,
        context: EmployeePayrollContext,
        weekly_off_rules: Sequence[WeeklyOffRule],
    ) -> PayDayMap:
        att_by_date: dict[date, Attendance] = {
            a.date: a for a in context.attendance_records
        }
        holidays_set: set[date] = {h.date for h in context.holidays}

        hours_per_day: Decimal = context.employee.working_hours_per_day
        result: PayDayMap = {}

        current = period.start_date
        while current <= period.end_date:
            attendance = att_by_date.get(current)
            is_holiday = current in holidays_set
            is_woff = _is_weekly_off(current, weekly_off_rules)

            if attendance is not None:
                status = attendance.status
                if status == AttendanceStatus.PRESENT:
                    day_type = PayDayType.PAID
                    regular_hours = hours_per_day
                elif status == AttendanceStatus.PAID_LEAVE:
                    day_type = PayDayType.PAID
                    regular_hours = hours_per_day
                elif status == AttendanceStatus.UNPAID_LEAVE:
                    day_type = PayDayType.LOP
                    regular_hours = Decimal(0)
                elif status == AttendanceStatus.HALF_DAY:
                    day_type = PayDayType.HALF_PAID_HALF_LOP
                    regular_hours = hours_per_day / Decimal(2)
                else:
                    # Fallback: treat unknown status as LOP
                    day_type = PayDayType.LOP
                    regular_hours = Decimal(0)

                overtime_hours = attendance.overtime_hours
            else:
                overtime_hours = Decimal(0)
                if is_woff or is_holiday:
                    day_type = PayDayType.PAID
                    regular_hours = hours_per_day
                else:
                    day_type = PayDayType.LOP
                    regular_hours = Decimal(0)

            result[current] = DayPayInfo(
                date=current,
                day_type=day_type,
                regular_hours=regular_hours,
                overtime_hours=overtime_hours,
                is_weekly_off=is_woff,
                is_holiday=is_holiday,
            )
            current += timedelta(days=1)

        return result
