from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, List
from uuid import UUID

from app.attendances.domain.value_objects import AttendanceSummary
from app.employees.domain.entities import Employee
from app.payroll.domain.entities import PayrollAdjustment, PayrollLineItem, PayrollRun
from app.payroll.domain.value_objects import (
    BusinessPayrollConfiguration,
    PayrollPeriod,
    PayrollStatus,
    AdjustmentType,
)
from app.payroll.domain.exceptions import (
    InvalidPayrollConfigurationError,
    PayrollCalculationError,
)


def _compute_period_start(label_year: int, label_month: int, payroll_start_date: int) -> date:
    """
    Compute the start date of the payroll period based on the label year, label month, and payroll start date.
    """
    try:
        return date(label_year, label_month, payroll_start_date)
    except ValueError as e:
        raise InvalidPayrollConfigurationError("Invalid payroll start date.") from e

def _compute_period_end(start_date: date, business_config: BusinessPayrollConfiguration) -> date:
    """
    Compute the end date of the payroll period based on the start date and business configuration.
    """
    # Calculate the next month and year
    if start_date.month == 12:
        next_month = 1
        next_year = start_date.year + 1
    else:
        next_month = start_date.month + 1
        next_year = start_date.year

    # Calculate the end date of the payroll period
    try:
        end_date = date(next_year, next_month, business_config.payroll_start_date) - timedelta(days=1)
    except ValueError as e:
        raise InvalidPayrollConfigurationError("Invalid payroll end date.") from e

    return end_date


@dataclass(slots=True)
class PayrollEngine:

    def compute_period(self, label_year: int, label_month: int, business_config: BusinessPayrollConfiguration) -> PayrollPeriod:
        """
        Compute the payroll period based on the label year, label month, and business configuration.
        """
        # Validate the business configuration
        if not business_config:
            raise InvalidPayrollConfigurationError("Business payroll configuration is missing.")

        # Calculate the start and end dates of the payroll period
        start_date = _compute_period_start(label_year, label_month, business_config.payroll_start_date)
        end_date = _compute_period_end(start_date, business_config)

        return PayrollPeriod(
            year=label_year,
            month=label_month,
            start_date=start_date,
            end_date=end_date,
        )
    
    def calculate_line_item(
        self,
        *,
        payroll_run_id: UUID,
        employee: Employee,
        attendance_summary: AttendanceSummary,
        adjustments: List[PayrollAdjustment],
        period: PayrollPeriod,
    ) -> PayrollLineItem:
        """
        Calculate the payroll line item for a given employee based on their attendance summary, adjustments, and payroll period.
        """
        if employee.salary_basis == "working_26_days":
            total_days_in_period = 26
        else:
            total_days_in_period = (period.end_date - period.start_date).days + 1

        if employee.wage_type == "daily":
            daily_rate = employee.wage_rate
            hourly_rate = daily_rate / employee.working_hours_per_day
        elif employee.wage_type == "hourly":
            hourly_rate = employee.wage_rate
            daily_rate = hourly_rate * employee.working_hours_per_day
        else:  # monthly
            daily_rate = employee.wage_rate / total_days_in_period
            hourly_rate = daily_rate / employee.working_hours_per_day

        overtime_pay = (attendance_summary.overtime_hours * hourly_rate * employee.overtime_multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        basic_pay = (
            (attendance_summary.present_days * daily_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            + (attendance_summary.half_days * daily_rate / 2).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            + (attendance_summary.paid_leave_days * daily_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            + (attendance_summary.paid_holiday_days * daily_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

        gross_pay = (basic_pay + overtime_pay).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        adjustments_bonus = Decimal(0.00)
        adjustments_deduction = Decimal(0.00)
        for adjustment in adjustments:
            if adjustment.adjustment_type == AdjustmentType.BONUS:
                adjustments_bonus += adjustment.amount
            elif adjustment.adjustment_type == AdjustmentType.DEDUCTION:
                adjustments_deduction += adjustment.amount

        net_pay = (gross_pay + adjustments_bonus - adjustments_deduction).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return PayrollLineItem(
            payroll_run_id=payroll_run_id,
            employee_id=employee.id,
            employee_name=employee.name,
            designation=employee.designation,
            present_days=attendance_summary.present_days,
            half_days=attendance_summary.half_days,
            paid_leave_days=attendance_summary.paid_leave_days,
            unpaid_leave_days=attendance_summary.unpaid_leave_days,
            paid_holiday_days=attendance_summary.paid_holiday_days,
            unpaid_holiday_days=attendance_summary.unpaid_holiday_days,
            overtime_hours=attendance_summary.overtime_hours,
            total_worked_hours=attendance_summary.total_worked_hours,
            basic_pay=basic_pay,
            overtime_pay=overtime_pay,
            gross_pay=gross_pay,
            adjustments_bonus=adjustments_bonus,
            adjustments_deduction=adjustments_deduction,
            net_pay=net_pay,
        )
        
    
    def calculate_run(
            self,
            *,
            label_year: int,
            label_month: int,
            business_config: BusinessPayrollConfiguration,
            employees: Iterable[Employee],
            attendance_summaries_by_employees: Dict[UUID, AttendanceSummary],
            adjustments_data: Dict[UUID, List[PayrollAdjustment]],
    ) -> PayrollRun:
        """
        Calculate the payroll run for a given period, business configuration, employees, attendance data, and adjustments data.
        """
        period = self.compute_period(label_year, label_month, business_config)

        payroll_run = PayrollRun(
            business_id=business_config.business_id,
            payroll_period=period,
            status=PayrollStatus.DRAFT,
            created_at=datetime.now(),
        )

        for employee in employees:
            attendance_summary = attendance_summaries_by_employees.get(employee.id)
            if not attendance_summary:
                raise PayrollCalculationError(f"Missing attendance summary for employee {employee.id}")

            adjustments = adjustments_data.get(employee.id, [])
            payroll_run.add_adjustments(adjustments)  # Add adjustments to the payroll run

            # Calculate the payroll line item for the employee
            line_item = self.calculate_line_item(
                payroll_run_id=payroll_run.id,
                employee=employee,
                attendance_summary=attendance_summary,
                adjustments=adjustments,
                period=period,
            )
            payroll_run.add_line_item(line_item)

        return payroll_run