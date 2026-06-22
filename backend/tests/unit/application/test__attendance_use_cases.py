# tests/unit/application/test__attendance_use_cases.py
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.attendance.application.commands import (
    BulkAttendanceEntry,
    BulkMarkAttendanceCommand,
    DeleteAttendanceCommand,
    GetAttendanceCommand,
    ListAttendanceByDateCommand,
    ListAttendanceByEmployeeCommand,
    MarkAllPresentCommand,
    MarkAttendanceCommand,
    UpdateAttendanceCommand,
)
from app.attendance.application.use_cases import (
    BulkMarkAttendanceUseCase,
    DeleteAttendanceUseCase,
    GetAttendanceUseCase,
    ListAttendanceByDateUseCase,
    ListAttendanceByEmployeeUseCase,
    MarkAllPresentUseCase,
    MarkAttendanceUseCase,
    UpdateAttendanceUseCase,
)
from app.attendance.domain.entities import Attendance, AttendanceStatus
from app.attendance.domain.exceptions import (
    AttendanceAlreadyExistsError,
    AttendanceFutureDateError,
    AttendanceNotFoundError,
    AttendanceOnHolidayError,
    AttendanceOnWeeklyOffError,
    InactiveEmployeeAttendanceError,
    OvertimeNotAllowedError,
)
from app.business.domain.entities import WageType
from app.business.domain.exceptions import BusinessNotFoundError
from app.employees.domain.entities import Employee
from app.employees.domain.exceptions import EmployeeNotFoundError

# PAST_DATE: in the past, not a holiday, not a weekly off (Wednesday)
# business_defaults has Monday (every week) and 2nd Tuesday as weekly off;
# June 10 = Wednesday, safe for all marking tests.
PAST_DATE = date(2026, 6, 10)
# HOLIDAY_DATE: seeded as New Year's Day in in_memory_holiday_repo
HOLIDAY_DATE = date(2026, 1, 1)
# FUTURE_DATE: beyond today (2026-06-22)
FUTURE_DATE = date(2026, 12, 31)
# WEEKLY_OFF_DATE: June 8 = Monday, which is a weekly off per business_defaults
WEEKLY_OFF_DATE = date(2026, 6, 8)


# ─── MarkAttendanceUseCase ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__mark_attendance_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )

    attendance = await use_case.execute(cmd)

    assert attendance.employee_id == employee.id
    assert attendance.date == PAST_DATE
    assert attendance.status == AttendanceStatus.PRESENT
    assert attendance.overtime_hours == Decimal("0")
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__mark_attendance_with_overtime(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
        overtime_hours=Decimal("2.5"),
    )

    attendance = await use_case.execute(cmd)

    assert attendance.overtime_hours == Decimal("2.5")
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__mark_attendance_paid_leave(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PAID_LEAVE,
    )

    attendance = await use_case.execute(cmd)

    assert attendance.status == AttendanceStatus.PAID_LEAVE
    assert attendance.overtime_hours == Decimal("0")


@pytest.mark.asyncio
async def test__mark_attendance_wrong_owner_raises_error(
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id="wrong-owner",
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)

    assert in_memory_uow.committed is False


@pytest.mark.asyncio
async def test__mark_attendance_future_date_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=FUTURE_DATE,
        status=AttendanceStatus.PRESENT,
    )

    with pytest.raises(AttendanceFutureDateError):
        await use_case.execute(cmd)

    assert in_memory_uow.committed is False


@pytest.mark.asyncio
async def test__mark_attendance_on_holiday_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=HOLIDAY_DATE,
        status=AttendanceStatus.PRESENT,
    )

    with pytest.raises(AttendanceOnHolidayError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__mark_attendance_employee_not_found_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=uuid4(),
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )

    with pytest.raises(EmployeeNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__mark_attendance_inactive_employee_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]
    employee = in_memory_employee_repo._items[0]
    employee.deactivate()

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )

    with pytest.raises(InactiveEmployeeAttendanceError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__mark_attendance_duplicate_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )
    await in_memory_attendance_repo.add(existing)

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PAID_LEAVE,
    )

    with pytest.raises(AttendanceAlreadyExistsError):
        await use_case.execute(cmd)


# ─── UpdateAttendanceUseCase ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__update_attendance_status(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )
    await in_memory_attendance_repo.add(existing)

    use_case = UpdateAttendanceUseCase(uow=in_memory_uow)
    cmd = UpdateAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
        fields_to_update=frozenset({"status"}),
        status=AttendanceStatus.PAID_LEAVE,
    )

    updated = await use_case.execute(cmd)

    assert updated.status == AttendanceStatus.PAID_LEAVE
    # status changed away from PRESENT → overtime cleared
    assert updated.overtime_hours == Decimal("0")
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__update_attendance_set_overtime(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )
    await in_memory_attendance_repo.add(existing)

    use_case = UpdateAttendanceUseCase(uow=in_memory_uow)
    cmd = UpdateAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
        fields_to_update=frozenset({"overtime_hours"}),
        overtime_hours=Decimal("3.0"),
    )

    updated = await use_case.execute(cmd)

    assert updated.overtime_hours == Decimal("3.0")
    assert updated.status == AttendanceStatus.PRESENT
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__update_attendance_reset_overtime_to_zero(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
        overtime_hours=Decimal("2.0"),
    )
    await in_memory_attendance_repo.add(existing)

    use_case = UpdateAttendanceUseCase(uow=in_memory_uow)
    cmd = UpdateAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
        fields_to_update=frozenset({"overtime_hours"}),
        overtime_hours=Decimal("0"),
    )

    updated = await use_case.execute(cmd)

    assert updated.overtime_hours == Decimal("0")
    assert updated.status == AttendanceStatus.PRESENT


@pytest.mark.asyncio
async def test__update_attendance_status_to_non_present_clears_overtime(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
        overtime_hours=Decimal("2.0"),
    )
    await in_memory_attendance_repo.add(existing)

    use_case = UpdateAttendanceUseCase(uow=in_memory_uow)
    cmd = UpdateAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
        fields_to_update=frozenset({"status"}),
        status=AttendanceStatus.HALF_DAY,
    )

    updated = await use_case.execute(cmd)

    assert updated.status == AttendanceStatus.HALF_DAY
    assert updated.overtime_hours == Decimal("0")


@pytest.mark.asyncio
async def test__update_attendance_overtime_on_non_present_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.HALF_DAY,
    )
    await in_memory_attendance_repo.add(existing)

    use_case = UpdateAttendanceUseCase(uow=in_memory_uow)
    cmd = UpdateAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
        fields_to_update=frozenset({"overtime_hours"}),
        overtime_hours=Decimal("2.0"),
    )

    with pytest.raises(OvertimeNotAllowedError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__update_attendance_not_found_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = UpdateAttendanceUseCase(uow=in_memory_uow)
    cmd = UpdateAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
        fields_to_update=frozenset({"status"}),
        status=AttendanceStatus.PAID_LEAVE,
    )

    with pytest.raises(AttendanceNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__update_attendance_wrong_owner_raises_error(
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )
    await in_memory_attendance_repo.add(existing)

    use_case = UpdateAttendanceUseCase(uow=in_memory_uow)
    cmd = UpdateAttendanceCommand(
        business_id=business.id,
        owner_id="wrong-owner",
        employee_id=employee.id,
        date=PAST_DATE,
        fields_to_update=frozenset({"status"}),
        status=AttendanceStatus.PAID_LEAVE,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)

    assert in_memory_uow.committed is False


# ─── DeleteAttendanceUseCase ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__delete_attendance_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )
    await in_memory_attendance_repo.add(existing)

    use_case = DeleteAttendanceUseCase(uow=in_memory_uow)
    cmd = DeleteAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
    )

    await use_case.execute(cmd)

    assert in_memory_uow.committed is True
    remaining = await in_memory_attendance_repo.list_by_date(
        business_id=business.id, date_=PAST_DATE
    )
    assert len(remaining) == 0


@pytest.mark.asyncio
async def test__delete_attendance_not_found_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = DeleteAttendanceUseCase(uow=in_memory_uow)
    cmd = DeleteAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
    )

    with pytest.raises(AttendanceNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__delete_attendance_wrong_owner_raises_error(
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )
    await in_memory_attendance_repo.add(existing)

    use_case = DeleteAttendanceUseCase(uow=in_memory_uow)
    cmd = DeleteAttendanceCommand(
        business_id=business.id,
        owner_id="wrong-owner",
        employee_id=employee.id,
        date=PAST_DATE,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)

    assert in_memory_uow.committed is False


# ─── GetAttendanceUseCase ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__get_attendance_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PAID_LEAVE,
    )
    await in_memory_attendance_repo.add(existing)

    use_case = GetAttendanceUseCase(uow=in_memory_uow)
    cmd = GetAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
    )

    fetched = await use_case.execute(cmd)

    assert fetched.employee_id == employee.id
    assert fetched.status == AttendanceStatus.PAID_LEAVE


@pytest.mark.asyncio
async def test__get_attendance_not_found_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = GetAttendanceUseCase(uow=in_memory_uow)
    cmd = GetAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=PAST_DATE,
    )

    with pytest.raises(AttendanceNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__get_attendance_wrong_owner_raises_error(
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )
    await in_memory_attendance_repo.add(existing)

    use_case = GetAttendanceUseCase(uow=in_memory_uow)
    cmd = GetAttendanceCommand(
        business_id=business.id,
        owner_id="wrong-owner",
        employee_id=employee.id,
        date=PAST_DATE,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)


# ─── ListAttendanceByDateUseCase ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test__list_attendance_by_date_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    a1 = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )
    await in_memory_attendance_repo.add(a1)

    use_case = ListAttendanceByDateUseCase(uow=in_memory_uow)
    cmd = ListAttendanceByDateCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=PAST_DATE,
    )

    records = await use_case.execute(cmd)

    assert len(records) == 1
    assert records[0].employee_id == employee.id


@pytest.mark.asyncio
async def test__list_attendance_by_date_filters_by_status(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    other_emp = Employee.create(
        id=uuid4(),
        business_id=business.id,
        name="Jane Doe",
        designation=None,
        wage_type=WageType.DAILY,
        wage_rate=Decimal("800.00"),
        working_hours_per_day=Decimal("8.0"),
        overtime_multiplier=Decimal("1.5"),
    )
    await in_memory_employee_repo.add(other_emp)

    a1 = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )
    a2 = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=other_emp.id,
        date=PAST_DATE,
        status=AttendanceStatus.PAID_LEAVE,
    )
    await in_memory_attendance_repo.add(a1)
    await in_memory_attendance_repo.add(a2)

    use_case = ListAttendanceByDateUseCase(uow=in_memory_uow)
    cmd = ListAttendanceByDateCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
    )

    records = await use_case.execute(cmd)

    assert len(records) == 1
    assert records[0].status == AttendanceStatus.PRESENT


@pytest.mark.asyncio
async def test__list_attendance_by_date_returns_empty_when_none(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = ListAttendanceByDateUseCase(uow=in_memory_uow)
    cmd = ListAttendanceByDateCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=PAST_DATE,
    )

    records = await use_case.execute(cmd)

    assert list(records) == []


@pytest.mark.asyncio
async def test__list_attendance_by_date_wrong_owner_raises_error(
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]

    use_case = ListAttendanceByDateUseCase(uow=in_memory_uow)
    cmd = ListAttendanceByDateCommand(
        business_id=business.id,
        owner_id="wrong-owner",
        date=PAST_DATE,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)


# ─── ListAttendanceByEmployeeUseCase ──────────────────────────────────────────


@pytest.mark.asyncio
async def test__list_attendance_by_employee_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    for day in [1, 2, 3]:
        a = Attendance.create(
            id=uuid4(),
            business_id=business.id,
            employee_id=employee.id,
            date=date(2026, 6, day),
            status=AttendanceStatus.PRESENT,
        )
        await in_memory_attendance_repo.add(a)

    use_case = ListAttendanceByEmployeeUseCase(uow=in_memory_uow)
    cmd = ListAttendanceByEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
    )

    records = await use_case.execute(cmd)

    assert len(records) == 3
    assert records[0].date == date(2026, 6, 1)
    assert records[-1].date == date(2026, 6, 3)


@pytest.mark.asyncio
async def test__list_attendance_by_employee_date_range_filter(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    for day in [1, 2, 3, 4, 5]:
        a = Attendance.create(
            id=uuid4(),
            business_id=business.id,
            employee_id=employee.id,
            date=date(2026, 6, day),
            status=AttendanceStatus.PRESENT,
        )
        await in_memory_attendance_repo.add(a)

    use_case = ListAttendanceByEmployeeUseCase(uow=in_memory_uow)
    cmd = ListAttendanceByEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        start_date=date(2026, 6, 2),
        end_date=date(2026, 6, 4),
    )

    records = await use_case.execute(cmd)

    assert len(records) == 3
    assert records[0].date == date(2026, 6, 2)
    assert records[-1].date == date(2026, 6, 4)


@pytest.mark.asyncio
async def test__list_attendance_by_employee_status_filter(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    for day, status in [
        (1, AttendanceStatus.PRESENT),
        (2, AttendanceStatus.UNPAID_LEAVE),
        (3, AttendanceStatus.PRESENT),
    ]:
        a = Attendance.create(
            id=uuid4(),
            business_id=business.id,
            employee_id=employee.id,
            date=date(2026, 6, day),
            status=status,
        )
        await in_memory_attendance_repo.add(a)

    use_case = ListAttendanceByEmployeeUseCase(uow=in_memory_uow)
    cmd = ListAttendanceByEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        status=AttendanceStatus.PRESENT,
    )

    records = await use_case.execute(cmd)

    assert len(records) == 2
    assert all(r.status == AttendanceStatus.PRESENT for r in records)


@pytest.mark.asyncio
async def test__list_attendance_by_employee_not_found_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = ListAttendanceByEmployeeUseCase(uow=in_memory_uow)
    cmd = ListAttendanceByEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=uuid4(),
    )

    with pytest.raises(EmployeeNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__list_attendance_by_employee_wrong_owner_raises_error(
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]

    use_case = ListAttendanceByEmployeeUseCase(uow=in_memory_uow)
    cmd = ListAttendanceByEmployeeCommand(
        business_id=business.id,
        owner_id="wrong-owner",
        employee_id=employee.id,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)


# ─── BulkMarkAttendanceUseCase ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__bulk_mark_attendance_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = BulkMarkAttendanceUseCase(uow=in_memory_uow)
    cmd = BulkMarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=PAST_DATE,
        entries=[
            BulkAttendanceEntry(
                employee_id=employee.id,
                status=AttendanceStatus.PRESENT,
                overtime_hours=Decimal("1.0"),
            )
        ],
    )

    results = await use_case.execute(cmd)

    assert len(results) == 1
    assert results[0].employee_id == employee.id
    assert results[0].overtime_hours == Decimal("1.0")
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__bulk_mark_attendance_overwrites_existing(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PRESENT,
        overtime_hours=Decimal("1.0"),
    )
    await in_memory_attendance_repo.add(existing)

    use_case = BulkMarkAttendanceUseCase(uow=in_memory_uow)
    cmd = BulkMarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=PAST_DATE,
        entries=[
            BulkAttendanceEntry(
                employee_id=employee.id,
                status=AttendanceStatus.PAID_LEAVE,
                overtime_hours=Decimal("0"),
            )
        ],
    )

    results = await use_case.execute(cmd)

    assert len(results) == 1
    assert results[0].status == AttendanceStatus.PAID_LEAVE
    assert results[0].overtime_hours == Decimal("0")


@pytest.mark.asyncio
async def test__bulk_mark_attendance_holiday_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = BulkMarkAttendanceUseCase(uow=in_memory_uow)
    cmd = BulkMarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=HOLIDAY_DATE,
        entries=[
            BulkAttendanceEntry(
                employee_id=employee.id, status=AttendanceStatus.PRESENT
            )
        ],
    )

    with pytest.raises(AttendanceOnHolidayError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__bulk_mark_attendance_future_date_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = BulkMarkAttendanceUseCase(uow=in_memory_uow)
    cmd = BulkMarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=FUTURE_DATE,
        entries=[
            BulkAttendanceEntry(
                employee_id=employee.id, status=AttendanceStatus.PRESENT
            )
        ],
    )

    with pytest.raises(AttendanceFutureDateError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__bulk_mark_attendance_inactive_employee_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]
    employee = in_memory_employee_repo._items[0]
    employee.deactivate()

    use_case = BulkMarkAttendanceUseCase(uow=in_memory_uow)
    cmd = BulkMarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=PAST_DATE,
        entries=[
            BulkAttendanceEntry(
                employee_id=employee.id, status=AttendanceStatus.PRESENT
            )
        ],
    )

    with pytest.raises(InactiveEmployeeAttendanceError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__bulk_mark_attendance_wrong_owner_raises_error(
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]

    use_case = BulkMarkAttendanceUseCase(uow=in_memory_uow)
    cmd = BulkMarkAttendanceCommand(
        business_id=business.id,
        owner_id="wrong-owner",
        date=PAST_DATE,
        entries=[
            BulkAttendanceEntry(
                employee_id=employee.id, status=AttendanceStatus.PRESENT
            )
        ],
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)


# ─── MarkAllPresentUseCase ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__mark_all_present_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = MarkAllPresentUseCase(uow=in_memory_uow)
    cmd = MarkAllPresentCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=PAST_DATE,
    )

    results = await use_case.execute(cmd)

    # One active employee is seeded by the fixture
    assert len(results) == 1
    assert results[0].status == AttendanceStatus.PRESENT
    assert results[0].overtime_hours == Decimal("0")
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__mark_all_present_no_active_employees_returns_empty(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]
    in_memory_employee_repo._items[0].deactivate()

    use_case = MarkAllPresentUseCase(uow=in_memory_uow)
    cmd = MarkAllPresentCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=PAST_DATE,
    )

    results = await use_case.execute(cmd)

    assert list(results) == []


@pytest.mark.asyncio
async def test__mark_all_present_holiday_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = MarkAllPresentUseCase(uow=in_memory_uow)
    cmd = MarkAllPresentCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=HOLIDAY_DATE,
    )

    with pytest.raises(AttendanceOnHolidayError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__mark_all_present_future_date_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = MarkAllPresentUseCase(uow=in_memory_uow)
    cmd = MarkAllPresentCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=FUTURE_DATE,
    )

    with pytest.raises(AttendanceFutureDateError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__mark_all_present_overwrites_existing(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
    in_memory_attendance_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    existing = Attendance.create(
        id=uuid4(),
        business_id=business.id,
        employee_id=employee.id,
        date=PAST_DATE,
        status=AttendanceStatus.PAID_LEAVE,
    )
    await in_memory_attendance_repo.add(existing)

    use_case = MarkAllPresentUseCase(uow=in_memory_uow)
    cmd = MarkAllPresentCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=PAST_DATE,
    )

    results = await use_case.execute(cmd)

    assert len(results) == 1
    assert results[0].status == AttendanceStatus.PRESENT


@pytest.mark.asyncio
async def test__mark_all_present_wrong_owner_raises_error(
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]

    use_case = MarkAllPresentUseCase(uow=in_memory_uow)
    cmd = MarkAllPresentCommand(
        business_id=business.id,
        owner_id="wrong-owner",
        date=PAST_DATE,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)


# ─── Weekly Off restriction ───────────────────────────────────────────────────
# business_defaults seeds MONDAY (every week) and 2nd TUESDAY as weekly off.
# WEEKLY_OFF_DATE = date(2026, 6, 8) is a Monday.


@pytest.mark.asyncio
async def test__mark_attendance_on_weekly_off_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=WEEKLY_OFF_DATE,
        status=AttendanceStatus.PRESENT,
    )

    with pytest.raises(AttendanceOnWeeklyOffError):
        await use_case.execute(cmd)

    assert in_memory_uow.committed is False


@pytest.mark.asyncio
async def test__mark_attendance_on_specific_week_weekly_off_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    """business_defaults has the 2nd Tuesday as weekly off.
    June 9, 2026 is the 2nd Tuesday of June."""
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]
    second_tuesday = date(2026, 6, 9)  # 2nd Tuesday of June 2026

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=second_tuesday,
        status=AttendanceStatus.PRESENT,
    )

    with pytest.raises(AttendanceOnWeeklyOffError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__mark_attendance_on_non_weekly_off_tuesday_succeeds(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    """The 3rd Tuesday of June (June 16) is NOT a weekly off — only the 2nd is."""
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]
    third_tuesday = date(2026, 6, 16)  # 3rd Tuesday of June 2026

    use_case = MarkAttendanceUseCase(uow=in_memory_uow)
    cmd = MarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=third_tuesday,
        status=AttendanceStatus.PRESENT,
    )

    attendance = await use_case.execute(cmd)

    assert attendance.status == AttendanceStatus.PRESENT
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__bulk_mark_attendance_on_weekly_off_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_employee_repo,
):
    business = in_memory_business_repo._items[0]
    employee = in_memory_employee_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = BulkMarkAttendanceUseCase(uow=in_memory_uow)
    cmd = BulkMarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=WEEKLY_OFF_DATE,
        entries=[
            BulkAttendanceEntry(
                employee_id=employee.id, status=AttendanceStatus.PRESENT
            )
        ],
    )

    with pytest.raises(AttendanceOnWeeklyOffError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__mark_all_present_on_weekly_off_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = MarkAllPresentUseCase(uow=in_memory_uow)
    cmd = MarkAllPresentCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=WEEKLY_OFF_DATE,
    )

    with pytest.raises(AttendanceOnWeeklyOffError):
        await use_case.execute(cmd)
