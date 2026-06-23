from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from app.business.domain.value_objects import SalaryBasis, WageType  # noqa: F401  (re-exported)


class PayDayType(StrEnum):
    PAID = "paid"
    LOP = "lop"
    HALF_PAID_HALF_LOP = "half_paid_half_lop"


@dataclass(frozen=True)
class PayrollPeriod:
    start_date: date
    end_date: date  # inclusive

    @classmethod
    def from_year_month(
        cls,
        year: int,
        month: int,
        payroll_start_day: int,
    ) -> "PayrollPeriod":
        """
        Derive the [start_date, end_date] inclusive period.

        - payroll_start_day == 1 → first..last calendar day of the given month.
        - otherwise → year-month-payroll_start_day .. day before next period start.
        """
        if payroll_start_day == 1:
            last_day = calendar.monthrange(year, month)[1]
            return cls(
                start_date=date(year, month, 1),
                end_date=date(year, month, last_day),
            )

        start = date(year, month, payroll_start_day)

        # next month
        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1

        from datetime import timedelta

        next_start = date(next_year, next_month, payroll_start_day)
        end = next_start - timedelta(days=1)

        return cls(start_date=start, end_date=end)


@dataclass(frozen=True)
class DayPayInfo:
    date: date
    day_type: PayDayType
    regular_hours: Decimal
    overtime_hours: Decimal
    is_weekly_off: bool
    is_holiday: bool


PayDayMap = dict[date, DayPayInfo]
