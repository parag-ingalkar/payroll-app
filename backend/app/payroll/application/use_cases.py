from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.business.domain.exceptions import BusinessNotFoundError
from app.core.uow import UnitOfWorkPort
from app.payroll.domain.day_classifier import DayClassifier, EmployeePayrollContext
from app.payroll.domain.engine import PayrollCalculationEngine
from app.payroll.domain.entities import PayrollRun, PayrollRunStatus
from app.payroll.domain.exceptions import PayrollRunNotFoundError
from app.payroll.domain.value_objects import PayDayMap, PayDayType, PayrollPeriod

from .commands import GetPayrollRunCommand, ListPayrollRunsCommand, RunPayrollCommand


def _has_missing_attendance(
    period: PayrollPeriod,
    day_map: PayDayMap,
) -> bool:
    """
    A day is "missing" when it is a plain working day (not weekly-off, not holiday)
    AND the day_type resolved to LOP because there was no attendance record.
    We detect this by checking days where is_weekly_off=False, is_holiday=False,
    and day_type=LOP (which in the classifier means no attendance on a working day).
    """
    from datetime import timedelta

    current = period.start_date
    while current <= period.end_date:
        info = day_map[current]
        if (
            not info.is_weekly_off
            and not info.is_holiday
            and info.day_type == PayDayType.LOP
            and info.regular_hours == 0
        ):
            return True
        current += timedelta(days=1)
    return False


@dataclass
class RunPayrollUseCase:
    uow: UnitOfWorkPort
    engine: PayrollCalculationEngine

    async def execute(self, cmd: RunPayrollCommand) -> PayrollRun:
        async with self.uow as uow:
            # Ownership check
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id,
                owner_id=cmd.owner_id,
            )
            if business is None:
                raise BusinessNotFoundError(
                    f"Business {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            period = PayrollPeriod.from_year_month(
                cmd.year,
                cmd.month,
                business.payroll_start_day,
            )

            if cmd.employee_ids is None:
                employees = await uow.employees.list_active_for_business(
                    cmd.business_id
                )
            else:
                employees = await uow.employees.list_by_ids(
                    cmd.business_id, cmd.employee_ids
                )

            weekly_off_rules = await uow.businesses.get_weekly_off_rules(
                cmd.business_id
            )
            holidays = await uow.holidays.list_for_period(
                cmd.business_id, period.start_date, period.end_date
            )

            line_items = []
            is_incomplete = False
            run_id = uuid4()
            now = datetime.now(tz=timezone.utc)

            for employee in employees:
                attendance = await uow.attendance.list_for_employee_and_period(
                    business_id=cmd.business_id,
                    employee_id=employee.id,
                    start_date=period.start_date,
                    end_date=period.end_date,
                )

                context = EmployeePayrollContext(
                    employee=employee,
                    business=business,
                    attendance_records=attendance,
                    holidays=holidays,
                )

                day_map = DayClassifier.classify_period(
                    period, context, weekly_off_rules
                )

                if _has_missing_attendance(period, day_map):
                    is_incomplete = True

                effective_basis = employee.salary_basis or business.default_salary_basis

                line_item = self.engine.calculate_employee(
                    period=period,
                    context=context,
                    day_pay_map=day_map,
                    salary_basis=effective_basis,
                    payroll_run_id=run_id,
                )
                line_items.append(line_item)

            # Replace any existing run for the period
            await uow.payroll.delete_for_period(cmd.business_id, period)

            run = PayrollRun(
                id=run_id,
                business_id=cmd.business_id,
                period=period,
                status=PayrollRunStatus.DRAFT,
                is_incomplete=is_incomplete,
                created_at=now,
                updated_at=now,
                line_items=line_items,
            )

            await uow.payroll.add(run)
            await uow.commit()

            return run


@dataclass
class GetPayrollRunUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: GetPayrollRunCommand) -> PayrollRun:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id,
                owner_id=cmd.owner_id,
            )
            if business is None:
                raise BusinessNotFoundError(
                    f"Business {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            run = await uow.payroll.get(cmd.business_id, cmd.run_id)
            if run is None:
                raise PayrollRunNotFoundError(
                    f"Payroll run {cmd.run_id} not found for business {cmd.business_id}."
                )
            return run


@dataclass
class ListPayrollRunsUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: ListPayrollRunsCommand) -> list[PayrollRun]:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id,
                owner_id=cmd.owner_id,
            )
            if business is None:
                raise BusinessNotFoundError(
                    f"Business {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            period: PayrollPeriod | None = None
            if cmd.year is not None and cmd.month is not None:
                period = PayrollPeriod.from_year_month(
                    cmd.year,
                    cmd.month,
                    business.payroll_start_day,
                )

            return await uow.payroll.list(
                business_id=cmd.business_id,
                period=period,
                employee_id=cmd.employee_id,
            )
