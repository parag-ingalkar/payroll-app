# tests/unit/application/test__payroll_use_cases.py
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.attendance.domain.entities import Attendance, AttendanceStatus
from app.business.domain.exceptions import BusinessNotFoundError
from app.payroll.application.commands import (
    GetPayrollRunCommand,
    ListPayrollRunsCommand,
    RunPayrollCommand,
)
from app.payroll.application.use_cases import (
    GetPayrollRunUseCase,
    ListPayrollRunsUseCase,
    RunPayrollUseCase,
)
from app.payroll.domain.engine import PayrollCalculationEngine
from app.payroll.domain.exceptions import PayrollRunNotFoundError

# ── RunPayrollUseCase ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__run_payroll_happy_path_creates_run(
    business_defaults,
    in_memory_uow,
):
    engine = PayrollCalculationEngine()
    use_case = RunPayrollUseCase(uow=in_memory_uow, engine=engine)

    business = in_memory_uow.businesses._items[0]
    employee = in_memory_uow.employees._items[0]

    for day in range(1, 32):
        in_memory_uow.attendance._items.append(
            Attendance.create(
                id=uuid4(),
                business_id=business.id,
                employee_id=employee.id,
                date=date(2026, 1, day),
                status=AttendanceStatus.PRESENT,
            )
        )

    cmd = RunPayrollCommand(
        business_id=business.id,
        owner_id=business_defaults["owner_id"],
        year=2026,
        month=1,
    )

    run = await use_case.execute(cmd)

    assert run.id is not None
    assert run.business_id == business.id
    assert len(run.line_items) == 1
    assert run.line_items[0].employee_id == employee.id
    assert run.line_items[0].gross_pay > Decimal("0")
    assert in_memory_uow.committed is True
    assert len(in_memory_uow.payroll._items) == 1


@pytest.mark.asyncio
async def test__run_payroll_wrong_owner_raises_business_not_found(
    in_memory_uow,
):
    engine = PayrollCalculationEngine()
    use_case = RunPayrollUseCase(uow=in_memory_uow, engine=engine)

    business = in_memory_uow.businesses._items[0]

    cmd = RunPayrollCommand(
        business_id=business.id,
        owner_id="wrong-owner",
        year=2026,
        month=1,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)

    assert in_memory_uow.committed is False


@pytest.mark.asyncio
async def test__run_payroll_unknown_business_raises_business_not_found(
    business_defaults,
    in_memory_uow,
):
    engine = PayrollCalculationEngine()
    use_case = RunPayrollUseCase(uow=in_memory_uow, engine=engine)

    cmd = RunPayrollCommand(
        business_id=uuid4(),
        owner_id=business_defaults["owner_id"],
        year=2026,
        month=1,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__run_payroll_marks_incomplete_when_attendance_missing(
    business_defaults,
    in_memory_uow,
):
    """A working day with no attendance record → is_incomplete=True."""
    engine = PayrollCalculationEngine()
    use_case = RunPayrollUseCase(uow=in_memory_uow, engine=engine)

    business = in_memory_uow.businesses._items[0]
    # Deliberately add NO attendance records

    cmd = RunPayrollCommand(
        business_id=business.id,
        owner_id=business_defaults["owner_id"],
        year=2026,
        month=1,
    )

    run = await use_case.execute(cmd)
    assert run.is_incomplete is True


@pytest.mark.asyncio
async def test__run_payroll_replaces_existing_run_for_same_period(
    business_defaults,
    in_memory_uow,
):
    """Running payroll twice for the same period replaces the first run."""
    engine = PayrollCalculationEngine()
    use_case = RunPayrollUseCase(uow=in_memory_uow, engine=engine)

    business = in_memory_uow.businesses._items[0]
    employee = in_memory_uow.employees._items[0]

    for day in range(1, 32):
        in_memory_uow.attendance._items.append(
            Attendance.create(
                id=uuid4(),
                business_id=business.id,
                employee_id=employee.id,
                date=date(2026, 1, day),
                status=AttendanceStatus.PRESENT,
            )
        )

    cmd = RunPayrollCommand(
        business_id=business.id,
        owner_id=business_defaults["owner_id"],
        year=2026,
        month=1,
    )

    await use_case.execute(cmd)
    in_memory_uow.committed = False
    await use_case.execute(cmd)

    period_runs = [
        r for r in in_memory_uow.payroll._items if r.business_id == business.id
    ]
    assert len(period_runs) == 1
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__run_payroll_with_specific_employee_ids(
    business_defaults,
    in_memory_uow,
):
    engine = PayrollCalculationEngine()
    use_case = RunPayrollUseCase(uow=in_memory_uow, engine=engine)

    business = in_memory_uow.businesses._items[0]
    employee = in_memory_uow.employees._items[0]

    for day in range(1, 32):
        in_memory_uow.attendance._items.append(
            Attendance.create(
                id=uuid4(),
                business_id=business.id,
                employee_id=employee.id,
                date=date(2026, 1, day),
                status=AttendanceStatus.PRESENT,
            )
        )

    cmd = RunPayrollCommand(
        business_id=business.id,
        owner_id=business_defaults["owner_id"],
        year=2026,
        month=1,
        employee_ids=[employee.id],
    )

    run = await use_case.execute(cmd)
    assert len(run.line_items) == 1
    assert run.line_items[0].employee_id == employee.id


# ── GetPayrollRunUseCase ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__get_payroll_run_happy_path(
    business_defaults,
    in_memory_uow,
):
    engine = PayrollCalculationEngine()
    run_uc = RunPayrollUseCase(uow=in_memory_uow, engine=engine)
    get_uc = GetPayrollRunUseCase(uow=in_memory_uow)

    business = in_memory_uow.businesses._items[0]
    employee = in_memory_uow.employees._items[0]

    for day in range(1, 32):
        in_memory_uow.attendance._items.append(
            Attendance.create(
                id=uuid4(),
                business_id=business.id,
                employee_id=employee.id,
                date=date(2026, 1, day),
                status=AttendanceStatus.PRESENT,
            )
        )

    created = await run_uc.execute(
        RunPayrollCommand(
            business_id=business.id,
            owner_id=business_defaults["owner_id"],
            year=2026,
            month=1,
        )
    )

    fetched = await get_uc.execute(
        GetPayrollRunCommand(
            business_id=business.id,
            owner_id=business_defaults["owner_id"],
            run_id=created.id,
        )
    )

    assert fetched.id == created.id
    assert fetched.business_id == business.id


@pytest.mark.asyncio
async def test__get_payroll_run_not_found_raises_error(
    business_defaults,
    in_memory_uow,
):
    get_uc = GetPayrollRunUseCase(uow=in_memory_uow)
    business = in_memory_uow.businesses._items[0]

    with pytest.raises(PayrollRunNotFoundError):
        await get_uc.execute(
            GetPayrollRunCommand(
                business_id=business.id,
                owner_id=business_defaults["owner_id"],
                run_id=uuid4(),
            )
        )


@pytest.mark.asyncio
async def test__get_payroll_run_wrong_owner_raises_business_not_found(
    in_memory_uow,
):
    get_uc = GetPayrollRunUseCase(uow=in_memory_uow)
    business = in_memory_uow.businesses._items[0]

    with pytest.raises(BusinessNotFoundError):
        await get_uc.execute(
            GetPayrollRunCommand(
                business_id=business.id,
                owner_id="wrong-owner",
                run_id=uuid4(),
            )
        )


# ── ListPayrollRunsUseCase ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__list_payroll_runs_returns_all_for_business(
    business_defaults,
    in_memory_uow,
):
    engine = PayrollCalculationEngine()
    run_uc = RunPayrollUseCase(uow=in_memory_uow, engine=engine)
    list_uc = ListPayrollRunsUseCase(uow=in_memory_uow)

    business = in_memory_uow.businesses._items[0]
    employee = in_memory_uow.employees._items[0]

    for month in [1, 2]:
        days_in_month = 31 if month == 1 else 28
        for day in range(1, days_in_month + 1):
            in_memory_uow.attendance._items.append(
                Attendance.create(
                    id=uuid4(),
                    business_id=business.id,
                    employee_id=employee.id,
                    date=date(2026, month, day),
                    status=AttendanceStatus.PRESENT,
                )
            )
        in_memory_uow.committed = False
        await run_uc.execute(
            RunPayrollCommand(
                business_id=business.id,
                owner_id=business_defaults["owner_id"],
                year=2026,
                month=month,
            )
        )

    runs = await list_uc.execute(
        ListPayrollRunsCommand(
            business_id=business.id,
            owner_id=business_defaults["owner_id"],
        )
    )
    assert len(runs) == 2


@pytest.mark.asyncio
async def test__list_payroll_runs_wrong_owner_raises_business_not_found(
    in_memory_uow,
):
    list_uc = ListPayrollRunsUseCase(uow=in_memory_uow)
    business = in_memory_uow.businesses._items[0]

    with pytest.raises(BusinessNotFoundError):
        await list_uc.execute(
            ListPayrollRunsCommand(
                business_id=business.id,
                owner_id="intruder",
            )
        )


@pytest.mark.asyncio
async def test__list_payroll_runs_filtered_by_year_month(
    business_defaults,
    in_memory_uow,
):
    engine = PayrollCalculationEngine()
    run_uc = RunPayrollUseCase(uow=in_memory_uow, engine=engine)
    list_uc = ListPayrollRunsUseCase(uow=in_memory_uow)

    business = in_memory_uow.businesses._items[0]
    employee = in_memory_uow.employees._items[0]

    for month in [1, 2]:
        days_in_month = 31 if month == 1 else 28
        for day in range(1, days_in_month + 1):
            in_memory_uow.attendance._items.append(
                Attendance.create(
                    id=uuid4(),
                    business_id=business.id,
                    employee_id=employee.id,
                    date=date(2026, month, day),
                    status=AttendanceStatus.PRESENT,
                )
            )
        in_memory_uow.committed = False
        await run_uc.execute(
            RunPayrollCommand(
                business_id=business.id,
                owner_id=business_defaults["owner_id"],
                year=2026,
                month=month,
            )
        )

    runs = await list_uc.execute(
        ListPayrollRunsCommand(
            business_id=business.id,
            owner_id=business_defaults["owner_id"],
            year=2026,
            month=1,
        )
    )
    assert len(runs) == 1
    assert runs[0].period.start_date.month == 1
