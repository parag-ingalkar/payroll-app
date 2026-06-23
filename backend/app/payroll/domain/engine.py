from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from app.business.domain.value_objects import SalaryBasis, WageType

from .day_classifier import EmployeePayrollContext
from .entities import PayrollLineItem
from .value_objects import PayDayMap, PayDayType, PayrollPeriod


class PayrollCalculationEngine:
    def calculate_employee(
        self,
        period: PayrollPeriod,
        context: EmployeePayrollContext,
        day_pay_map: PayDayMap,
        salary_basis: SalaryBasis,
        payroll_run_id: UUID,
    ) -> PayrollLineItem:
        employee = context.employee
        wage_type: WageType = employee.wage_type
        wage_rate: Decimal = employee.wage_rate
        hours_per_day: Decimal = employee.working_hours_per_day

        # 1. Basis days
        if salary_basis == SalaryBasis.CALENDAR_DAYS:
            basis_days = (period.end_date - period.start_date).days + 1
        elif salary_basis == SalaryBasis.FIXED_30_DAYS:
            basis_days = 30
        elif salary_basis == SalaryBasis.WORKING_26_DAYS:
            basis_days = 26
        else:
            basis_days = (period.end_date - period.start_date).days + 1

        # 2. Per-day / per-hour rate
        if wage_type == WageType.MONTHLY:
            per_day_rate = wage_rate / Decimal(basis_days)
            per_hour_rate = per_day_rate / hours_per_day
        elif wage_type == WageType.DAILY:
            per_day_rate = wage_rate
            per_hour_rate = wage_rate / hours_per_day
        else:  # HOURLY
            per_hour_rate = wage_rate
            per_day_rate = wage_rate * hours_per_day

        # 3. Aggregate over period
        paid_days = Decimal(0)
        lop_days = Decimal(0)
        weekly_off_days = 0
        holiday_days = 0
        total_regular_hours = Decimal(0)
        total_overtime_hours = Decimal(0)
        total_days_in_period = (period.end_date - period.start_date).days + 1

        current = period.start_date
        while current <= period.end_date:
            info = day_pay_map[current]

            if info.day_type == PayDayType.PAID:
                paid_days += Decimal(1)
            elif info.day_type == PayDayType.LOP:
                lop_days += Decimal(1)
            elif info.day_type == PayDayType.HALF_PAID_HALF_LOP:
                paid_days += Decimal("0.5")
                lop_days += Decimal("0.5")

            if info.is_weekly_off:
                weekly_off_days += 1
            if info.is_holiday:
                holiday_days += 1

            total_regular_hours += info.regular_hours
            total_overtime_hours += info.overtime_hours
            current += timedelta(days=1)

        # 4. Base pay
        if wage_type == WageType.MONTHLY:
            base_pay = wage_rate - per_day_rate * lop_days
        elif wage_type == WageType.DAILY:
            base_pay = per_day_rate * paid_days
        else:  # HOURLY
            base_pay = per_hour_rate * total_regular_hours

        # 5. Overtime pay
        overtime_pay = (
            per_hour_rate * employee.overtime_multiplier * total_overtime_hours
        )

        # 6. Gross
        gross_pay = base_pay + overtime_pay

        return PayrollLineItem(
            id=uuid4(),
            payroll_run_id=payroll_run_id,
            employee_id=employee.id,
            employee_name=employee.name,
            wage_type=wage_type,
            wage_rate=wage_rate,
            working_hours_per_day=hours_per_day,
            overtime_multiplier=employee.overtime_multiplier,
            salary_basis=salary_basis,
            basis_days=basis_days,
            total_days_in_period=total_days_in_period,
            paid_days=paid_days,
            lop_days=lop_days,
            weekly_off_days=weekly_off_days,
            holiday_days=holiday_days,
            overtime_hours=total_overtime_hours,
            per_day_rate=per_day_rate,
            per_hour_rate=per_hour_rate,
            base_pay=base_pay,
            overtime_pay=overtime_pay,
            gross_pay=gross_pay,
        )
