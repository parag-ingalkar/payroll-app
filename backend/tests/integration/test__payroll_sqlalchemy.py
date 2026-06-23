# tests/integration/test__payroll_sqlalchemy.py
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.attendance.domain.entities import Attendance, AttendanceStatus
from app.business.domain.entities import Business, WageType
from app.business.domain.value_objects import SalaryBasis
from app.core.uow import SqlAlchemyUnitOfWork
from app.employees.domain.entities import Employee
from app.payroll.application.commands import RunPayrollCommand
from app.payroll.application.use_cases import RunPayrollUseCase
from app.payroll.domain.engine import PayrollCalculationEngine
from app.payroll.domain.value_objects import PayrollPeriod

# ── in-uow seed helpers (never open a nested `async with`) ───────────────────


async def _seed_business(
    uow: SqlAlchemyUnitOfWork, owner_id: str = "owner-payroll"
) -> Business:
    business = Business.create(
        owner_id=owner_id,
        name=f"Payroll ORM Biz {uuid4().hex[:6]}",
        default_wage_type=WageType.MONTHLY,
        default_working_hours_per_day=Decimal("8.0"),
        default_overtime_multiplier=Decimal("1.5"),
        default_salary_basis=SalaryBasis.WORKING_26_DAYS,
        payroll_start_day=1,
        weekly_off_rules=[],
    )
    await uow.businesses.add(business)
    await uow.commit()
    return business


async def _seed_employee(uow: SqlAlchemyUnitOfWork, business: Business) -> Employee:
    employee = Employee.create(
        id=uuid4(),
        business_id=business.id,
        name="Test Worker",
        designation="Engineer",
        wage_type=WageType.MONTHLY,
        salary_basis=SalaryBasis.WORKING_26_DAYS,
        wage_rate=Decimal("30000.00"),
        working_hours_per_day=Decimal("8.0"),
        overtime_multiplier=Decimal("1.5"),
    )
    await uow.employees.add(employee)
    await uow.commit()
    return employee


async def _seed_attendance(
    uow: SqlAlchemyUnitOfWork,
    business: Business,
    employee: Employee,
    year: int,
    month: int,
    days: int,
):
    for d in range(1, days + 1):
        await uow.attendance.add(
            Attendance.create(
                id=uuid4(),
                business_id=business.id,
                employee_id=employee.id,
                date=date(year, month, d),
                status=AttendanceStatus.PRESENT,
            )
        )
    await uow.commit()


async def _run_payroll(
    uow: SqlAlchemyUnitOfWork,
    business: Business,
    year: int,
    month: int,
):
    engine = PayrollCalculationEngine()
    use_case = RunPayrollUseCase(lambda: uow, engine)
    return await use_case.execute(
        RunPayrollCommand(
            business_id=business.id,
            owner_id=business.owner_id,
            year=year,
            month=month,
        )
    )


# ── enum round-trip ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__payroll_run_enum_fields_survive_db_roundtrip(sqlalchemy_uow):
    """
    P0: SalaryBasis and WageType survive a write → read cycle.
    Catches the StrEnum/values_callable deserialization bug.
    """
    business = await _seed_business(sqlalchemy_uow)
    employee = await _seed_employee(sqlalchemy_uow, business)
    await _seed_attendance(sqlalchemy_uow, business, employee, 2026, 1, 26)

    run = await _run_payroll(sqlalchemy_uow, business, 2026, 1)

    fetched = await sqlalchemy_uow.payroll.get(business.id, run.id)

    assert fetched is not None
    line = fetched.line_items[0]
    assert line.wage_type == WageType.MONTHLY
    assert line.salary_basis == SalaryBasis.WORKING_26_DAYS


# ── add / get ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__run_payroll_persists_run_and_line_items(sqlalchemy_uow):
    """P0: Payroll run and line items are persisted and retrievable."""
    business = await _seed_business(sqlalchemy_uow)
    employee = await _seed_employee(sqlalchemy_uow, business)
    await _seed_attendance(sqlalchemy_uow, business, employee, 2026, 1, 26)

    run = await _run_payroll(sqlalchemy_uow, business, 2026, 1)

    fetched = await sqlalchemy_uow.payroll.get(business.id, run.id)

    assert fetched is not None
    assert fetched.id == run.id
    assert fetched.business_id == business.id
    assert len(fetched.line_items) == 1
    assert fetched.line_items[0].employee_id == employee.id
    assert fetched.line_items[0].gross_pay > Decimal("0")


@pytest.mark.asyncio
async def test__get_payroll_run_unknown_id_returns_none(sqlalchemy_uow):
    """P0: get() with a nonexistent run_id returns None."""
    business = await _seed_business(sqlalchemy_uow)

    result = await sqlalchemy_uow.payroll.get(business.id, uuid4())

    assert result is None


# ── list ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__list_payroll_runs_returns_all_for_business(sqlalchemy_uow):
    """P0: list() returns all runs for a business."""
    business = await _seed_business(sqlalchemy_uow)
    employee = await _seed_employee(sqlalchemy_uow, business)

    for month, days in [(1, 26), (2, 26)]:
        await _seed_attendance(sqlalchemy_uow, business, employee, 2026, month, days)
        await _run_payroll(sqlalchemy_uow, business, 2026, month)

    runs = await sqlalchemy_uow.payroll.list(business.id)

    assert len(runs) == 2
    assert {r.period.start_date.month for r in runs} == {1, 2}


@pytest.mark.asyncio
async def test__list_payroll_runs_filtered_by_period(sqlalchemy_uow):
    """P0: list() with a period filter returns only the matching run."""
    business = await _seed_business(sqlalchemy_uow)
    employee = await _seed_employee(sqlalchemy_uow, business)

    for month, days in [(1, 26), (2, 26)]:
        await _seed_attendance(sqlalchemy_uow, business, employee, 2026, month, days)
        await _run_payroll(sqlalchemy_uow, business, 2026, month)

    jan_period = PayrollPeriod.from_year_month(2026, 1, business.payroll_start_day)
    runs = await sqlalchemy_uow.payroll.list(business.id, period=jan_period)

    assert len(runs) == 1
    assert runs[0].period.start_date.month == 1


@pytest.mark.asyncio
async def test__list_payroll_runs_isolated_between_businesses(sqlalchemy_uow):
    """P0: list() never leaks runs from one business to another."""
    biz_a = await _seed_business(sqlalchemy_uow, owner_id=f"owner-a-{uuid4().hex[:4]}")
    biz_b = await _seed_business(sqlalchemy_uow, owner_id=f"owner-b-{uuid4().hex[:4]}")
    emp_a = await _seed_employee(sqlalchemy_uow, biz_a)

    await _seed_attendance(sqlalchemy_uow, biz_a, emp_a, 2026, 1, 26)
    await _run_payroll(sqlalchemy_uow, biz_a, 2026, 1)

    runs_b = await sqlalchemy_uow.payroll.list(biz_b.id)
    assert runs_b == []


# ── upsert ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__rerunning_payroll_replaces_previous_run(sqlalchemy_uow):
    """P0: Running payroll twice for the same period leaves exactly one run."""
    business = await _seed_business(sqlalchemy_uow)
    employee = await _seed_employee(sqlalchemy_uow, business)
    await _seed_attendance(sqlalchemy_uow, business, employee, 2026, 1, 26)

    first = await _run_payroll(sqlalchemy_uow, business, 2026, 1)
    second = await _run_payroll(sqlalchemy_uow, business, 2026, 1)

    assert first.id != second.id
    all_runs = await sqlalchemy_uow.payroll.list(business.id)
    assert len(all_runs) == 1
    assert all_runs[0].id == second.id


# ── cascade delete ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__line_items_cascade_delete_with_run(sqlalchemy_uow):
    """P0: delete_for_period removes the run and all its line items."""
    business = await _seed_business(sqlalchemy_uow)
    employee = await _seed_employee(sqlalchemy_uow, business)
    await _seed_attendance(sqlalchemy_uow, business, employee, 2026, 1, 26)

    run = await _run_payroll(sqlalchemy_uow, business, 2026, 1)
    period = PayrollPeriod.from_year_month(2026, 1, business.payroll_start_day)

    await sqlalchemy_uow.payroll.delete_for_period(business.id, period)
    await sqlalchemy_uow.commit()

    result = await sqlalchemy_uow.payroll.get(business.id, run.id)
    assert result is None
