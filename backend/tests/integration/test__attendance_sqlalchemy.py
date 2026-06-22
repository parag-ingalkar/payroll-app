# tests/integration/test__attendance_sqlalchemy.py
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
    AttendanceNotFoundError,
    AttendanceOnHolidayError,
)
from app.business.domain.entities import WageType
from app.business.domain.value_objects import SalaryBasis
from app.employees.domain.entities import Employee

ATTENDANCE_DATE = date(2026, 6, 10)
HOLIDAY_DATE = date(2026, 1, 1)  # seeded by add_business_and_holiday_in_db fixture


@pytest.mark.asyncio
async def test__mark_attendance(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    use_case = MarkAttendanceUseCase(sqlalchemy_uow)
    cmd = MarkAttendanceCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=ATTENDANCE_DATE,
        status=AttendanceStatus.PRESENT,
        overtime_hours=Decimal("1.5"),
    )

    created = await use_case.execute(cmd)

    assert created.employee_id == employee.id
    assert created.date == ATTENDANCE_DATE
    assert created.status == AttendanceStatus.PRESENT
    assert created.overtime_hours == Decimal("1.5")

    # Verify DB state
    async with sqlalchemy_uow as uow:
        reloaded = await uow.attendance.get_by_employee_and_date(
            business_id=employee.business_id,
            employee_id=employee.id,
            date_=ATTENDANCE_DATE,
        )
        assert reloaded is not None
        assert reloaded.status == AttendanceStatus.PRESENT
        assert reloaded.overtime_hours == Decimal("1.5")


@pytest.mark.asyncio
async def test__mark_attendance_on_holiday_raises_error(
    sqlalchemy_uow,
    add_business_and_holiday_in_db,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    use_case = MarkAttendanceUseCase(sqlalchemy_uow)
    cmd = MarkAttendanceCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=HOLIDAY_DATE,
        status=AttendanceStatus.PRESENT,
    )

    with pytest.raises(AttendanceOnHolidayError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__get_attendance(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    async with sqlalchemy_uow as uow:
        attendance = Attendance.create(
            id=uuid4(),
            business_id=employee.business_id,
            employee_id=employee.id,
            date=ATTENDANCE_DATE,
            status=AttendanceStatus.PAID_LEAVE,
        )
        await uow.attendance.add(attendance)
        await uow.commit()

    use_case = GetAttendanceUseCase(sqlalchemy_uow)
    cmd = GetAttendanceCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=ATTENDANCE_DATE,
    )

    fetched = await use_case.execute(cmd)

    assert fetched.employee_id == employee.id
    assert fetched.status == AttendanceStatus.PAID_LEAVE


@pytest.mark.asyncio
async def test__get_attendance_not_found_raises_error(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    use_case = GetAttendanceUseCase(sqlalchemy_uow)
    cmd = GetAttendanceCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=ATTENDANCE_DATE,
    )

    with pytest.raises(AttendanceNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__list_attendance_by_date(
    sqlalchemy_uow,
    add_business_in_db,
    business_defaults,
):
    business = add_business_in_db
    owner_id = business_defaults["owner_id"]

    async with sqlalchemy_uow as uow:
        emp1 = Employee.create(
            id=uuid4(),
            business_id=business.id,
            name="Alice",
            designation=None,
            wage_type=WageType.DAILY,
            wage_rate=Decimal("800.00"),
            working_hours_per_day=Decimal("8.0"),
            overtime_multiplier=Decimal("1.5"),
            salary_basis=SalaryBasis.WORKING_26_DAYS,
        )
        emp2 = Employee.create(
            id=uuid4(),
            business_id=business.id,
            name="Bob",
            designation=None,
            wage_type=WageType.DAILY,
            wage_rate=Decimal("800.00"),
            working_hours_per_day=Decimal("8.0"),
            overtime_multiplier=Decimal("1.5"),
            salary_basis=SalaryBasis.WORKING_26_DAYS,
        )
        await uow.employees.add(emp1)
        await uow.employees.add(emp2)
        await uow.commit()

    async with sqlalchemy_uow as uow:
        a1 = Attendance.create(
            id=uuid4(),
            business_id=business.id,
            employee_id=emp1.id,
            date=ATTENDANCE_DATE,
            status=AttendanceStatus.PRESENT,
        )
        a2 = Attendance.create(
            id=uuid4(),
            business_id=business.id,
            employee_id=emp2.id,
            date=ATTENDANCE_DATE,
            status=AttendanceStatus.PAID_LEAVE,
        )
        await uow.attendance.add(a1)
        await uow.attendance.add(a2)
        await uow.commit()

    list_uc = ListAttendanceByDateUseCase(sqlalchemy_uow)
    cmd = ListAttendanceByDateCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=ATTENDANCE_DATE,
    )

    records = await list_uc.execute(cmd)

    assert len(records) == 2


@pytest.mark.asyncio
async def test__list_attendance_by_date_status_filter(
    sqlalchemy_uow,
    add_business_in_db,
    business_defaults,
):
    business = add_business_in_db
    owner_id = business_defaults["owner_id"]

    async with sqlalchemy_uow as uow:
        emp1 = Employee.create(
            id=uuid4(),
            business_id=business.id,
            name="Alice",
            designation=None,
            wage_type=WageType.DAILY,
            wage_rate=Decimal("800.00"),
            working_hours_per_day=Decimal("8.0"),
            overtime_multiplier=Decimal("1.5"),
            salary_basis=SalaryBasis.WORKING_26_DAYS,
        )
        emp2 = Employee.create(
            id=uuid4(),
            business_id=business.id,
            name="Bob",
            designation=None,
            wage_type=WageType.DAILY,
            wage_rate=Decimal("800.00"),
            working_hours_per_day=Decimal("8.0"),
            overtime_multiplier=Decimal("1.5"),
            salary_basis=SalaryBasis.WORKING_26_DAYS,
        )
        await uow.employees.add(emp1)
        await uow.employees.add(emp2)
        await uow.commit()

    async with sqlalchemy_uow as uow:
        a1 = Attendance.create(
            id=uuid4(),
            business_id=business.id,
            employee_id=emp1.id,
            date=ATTENDANCE_DATE,
            status=AttendanceStatus.PRESENT,
        )
        a2 = Attendance.create(
            id=uuid4(),
            business_id=business.id,
            employee_id=emp2.id,
            date=ATTENDANCE_DATE,
            status=AttendanceStatus.PAID_LEAVE,
        )
        await uow.attendance.add(a1)
        await uow.attendance.add(a2)
        await uow.commit()

    list_uc = ListAttendanceByDateUseCase(sqlalchemy_uow)
    cmd = ListAttendanceByDateCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=ATTENDANCE_DATE,
        status=AttendanceStatus.PRESENT,
    )

    records = await list_uc.execute(cmd)

    assert len(records) == 1
    assert records[0].status == AttendanceStatus.PRESENT


@pytest.mark.asyncio
async def test__list_attendance_by_employee(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    async with sqlalchemy_uow as uow:
        for day in [1, 2, 3, 5]:
            a = Attendance.create(
                id=uuid4(),
                business_id=employee.business_id,
                employee_id=employee.id,
                date=date(2026, 6, day),
                status=AttendanceStatus.PRESENT,
            )
            await uow.attendance.add(a)
        await uow.commit()

    list_uc = ListAttendanceByEmployeeUseCase(sqlalchemy_uow)
    cmd = ListAttendanceByEmployeeCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
    )

    records = await list_uc.execute(cmd)

    assert len(records) == 4
    # Results ordered by date ascending
    assert records[0].date == date(2026, 6, 1)
    assert records[-1].date == date(2026, 6, 5)


@pytest.mark.asyncio
async def test__list_attendance_by_employee_date_range_filter(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    async with sqlalchemy_uow as uow:
        for day in [1, 2, 3, 4, 5]:
            a = Attendance.create(
                id=uuid4(),
                business_id=employee.business_id,
                employee_id=employee.id,
                date=date(2026, 6, day),
                status=AttendanceStatus.PRESENT,
            )
            await uow.attendance.add(a)
        await uow.commit()

    list_uc = ListAttendanceByEmployeeUseCase(sqlalchemy_uow)
    cmd = ListAttendanceByEmployeeCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
        start_date=date(2026, 6, 2),
        end_date=date(2026, 6, 4),
    )

    records = await list_uc.execute(cmd)

    assert len(records) == 3
    assert records[0].date == date(2026, 6, 2)
    assert records[-1].date == date(2026, 6, 4)


@pytest.mark.asyncio
async def test__update_attendance_status(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    async with sqlalchemy_uow as uow:
        attendance = Attendance.create(
            id=uuid4(),
            business_id=employee.business_id,
            employee_id=employee.id,
            date=ATTENDANCE_DATE,
            status=AttendanceStatus.PRESENT,
            overtime_hours=Decimal("2.0"),
        )
        await uow.attendance.add(attendance)
        await uow.commit()

    update_uc = UpdateAttendanceUseCase(sqlalchemy_uow)
    cmd = UpdateAttendanceCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=ATTENDANCE_DATE,
        fields_to_update=frozenset({"status"}),
        status=AttendanceStatus.PAID_LEAVE,
    )

    updated = await update_uc.execute(cmd)

    assert updated.status == AttendanceStatus.PAID_LEAVE
    assert updated.overtime_hours == Decimal("0")

    # Verify DB state
    async with sqlalchemy_uow as uow:
        reloaded = await uow.attendance.get_by_employee_and_date(
            business_id=employee.business_id,
            employee_id=employee.id,
            date_=ATTENDANCE_DATE,
        )
        assert reloaded is not None
        assert reloaded.status == AttendanceStatus.PAID_LEAVE
        assert reloaded.overtime_hours == Decimal("0")


@pytest.mark.asyncio
async def test__update_attendance_overtime(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    async with sqlalchemy_uow as uow:
        attendance = Attendance.create(
            id=uuid4(),
            business_id=employee.business_id,
            employee_id=employee.id,
            date=ATTENDANCE_DATE,
            status=AttendanceStatus.PRESENT,
        )
        await uow.attendance.add(attendance)
        await uow.commit()

    update_uc = UpdateAttendanceUseCase(sqlalchemy_uow)
    cmd = UpdateAttendanceCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=ATTENDANCE_DATE,
        fields_to_update=frozenset({"overtime_hours"}),
        overtime_hours=Decimal("3.5"),
    )

    updated = await update_uc.execute(cmd)

    assert updated.overtime_hours == Decimal("3.5")

    # Verify DB state
    async with sqlalchemy_uow as uow:
        reloaded = await uow.attendance.get_by_employee_and_date(
            business_id=employee.business_id,
            employee_id=employee.id,
            date_=ATTENDANCE_DATE,
        )
        assert reloaded is not None
        assert reloaded.overtime_hours == Decimal("3.5")


@pytest.mark.asyncio
async def test__delete_attendance(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    async with sqlalchemy_uow as uow:
        attendance = Attendance.create(
            id=uuid4(),
            business_id=employee.business_id,
            employee_id=employee.id,
            date=ATTENDANCE_DATE,
            status=AttendanceStatus.PRESENT,
        )
        await uow.attendance.add(attendance)
        await uow.commit()

    delete_uc = DeleteAttendanceUseCase(sqlalchemy_uow)
    cmd = DeleteAttendanceCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
        date=ATTENDANCE_DATE,
    )

    await delete_uc.execute(cmd)

    # Verify removal from DB
    async with sqlalchemy_uow as uow:
        reloaded = await uow.attendance.get_by_employee_and_date(
            business_id=employee.business_id,
            employee_id=employee.id,
            date_=ATTENDANCE_DATE,
        )
        assert reloaded is None


@pytest.mark.asyncio
async def test__bulk_mark_attendance_creates_records(
    sqlalchemy_uow,
    add_business_in_db,
    business_defaults,
):
    business = add_business_in_db
    owner_id = business_defaults["owner_id"]

    async with sqlalchemy_uow as uow:
        emp1 = Employee.create(
            id=uuid4(),
            business_id=business.id,
            name="Alice",
            designation=None,
            wage_type=WageType.DAILY,
            wage_rate=Decimal("800.00"),
            working_hours_per_day=Decimal("8.0"),
            overtime_multiplier=Decimal("1.5"),
            salary_basis=SalaryBasis.WORKING_26_DAYS,
        )
        emp2 = Employee.create(
            id=uuid4(),
            business_id=business.id,
            name="Bob",
            designation=None,
            wage_type=WageType.DAILY,
            wage_rate=Decimal("800.00"),
            working_hours_per_day=Decimal("8.0"),
            overtime_multiplier=Decimal("1.5"),
            salary_basis=SalaryBasis.WORKING_26_DAYS,
        )
        await uow.employees.add(emp1)
        await uow.employees.add(emp2)
        await uow.commit()

    bulk_uc = BulkMarkAttendanceUseCase(sqlalchemy_uow)
    cmd = BulkMarkAttendanceCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=ATTENDANCE_DATE,
        entries=[
            BulkAttendanceEntry(
                employee_id=emp1.id,
                status=AttendanceStatus.PRESENT,
                overtime_hours=Decimal("1.0"),
            ),
            BulkAttendanceEntry(
                employee_id=emp2.id, status=AttendanceStatus.PAID_LEAVE
            ),
        ],
    )

    results = await bulk_uc.execute(cmd)

    assert len(results) == 2

    # Verify DB state
    async with sqlalchemy_uow as uow:
        r1 = await uow.attendance.get_by_employee_and_date(
            business_id=business.id, employee_id=emp1.id, date_=ATTENDANCE_DATE
        )
        r2 = await uow.attendance.get_by_employee_and_date(
            business_id=business.id, employee_id=emp2.id, date_=ATTENDANCE_DATE
        )
        assert r1 is not None
        assert r1.status == AttendanceStatus.PRESENT
        assert r1.overtime_hours == Decimal("1.0")
        assert r2 is not None
        assert r2.status == AttendanceStatus.PAID_LEAVE


@pytest.mark.asyncio
async def test__bulk_mark_attendance_upserts_existing(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    # Seed an initial attendance record
    async with sqlalchemy_uow as uow:
        initial = Attendance.create(
            id=uuid4(),
            business_id=employee.business_id,
            employee_id=employee.id,
            date=ATTENDANCE_DATE,
            status=AttendanceStatus.PRESENT,
            overtime_hours=Decimal("2.0"),
        )
        await uow.attendance.add(initial)
        await uow.commit()

    # Bulk overwrite with a different status
    bulk_uc = BulkMarkAttendanceUseCase(sqlalchemy_uow)
    cmd = BulkMarkAttendanceCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        date=ATTENDANCE_DATE,
        entries=[
            BulkAttendanceEntry(
                employee_id=employee.id,
                status=AttendanceStatus.HALF_DAY,
                overtime_hours=Decimal("0"),
            )
        ],
    )

    results = await bulk_uc.execute(cmd)

    assert len(results) == 1
    assert results[0].status == AttendanceStatus.HALF_DAY
    assert results[0].overtime_hours == Decimal("0")

    # Verify DB state — only one record, with updated values
    async with sqlalchemy_uow as uow:
        reloaded = await uow.attendance.get_by_employee_and_date(
            business_id=employee.business_id,
            employee_id=employee.id,
            date_=ATTENDANCE_DATE,
        )
        assert reloaded is not None
        assert reloaded.status == AttendanceStatus.HALF_DAY


@pytest.mark.asyncio
async def test__mark_all_present(
    sqlalchemy_uow,
    add_business_in_db,
    business_defaults,
):
    business = add_business_in_db
    owner_id = business_defaults["owner_id"]

    async with sqlalchemy_uow as uow:
        emp1 = Employee.create(
            id=uuid4(),
            business_id=business.id,
            name="Alice",
            designation=None,
            wage_type=WageType.DAILY,
            wage_rate=Decimal("800.00"),
            working_hours_per_day=Decimal("8.0"),
            overtime_multiplier=Decimal("1.5"),
            salary_basis=SalaryBasis.WORKING_26_DAYS,
        )
        emp2 = Employee.create(
            id=uuid4(),
            business_id=business.id,
            name="Bob",
            designation=None,
            wage_type=WageType.DAILY,
            wage_rate=Decimal("800.00"),
            working_hours_per_day=Decimal("8.0"),
            overtime_multiplier=Decimal("1.5"),
            salary_basis=SalaryBasis.WORKING_26_DAYS,
        )
        inactive_emp = Employee.create(
            id=uuid4(),
            business_id=business.id,
            name="Inactive",
            designation=None,
            wage_type=WageType.DAILY,
            wage_rate=Decimal("800.00"),
            working_hours_per_day=Decimal("8.0"),
            overtime_multiplier=Decimal("1.5"),
            salary_basis=SalaryBasis.WORKING_26_DAYS,
        )
        inactive_emp.deactivate()
        await uow.employees.add(emp1)
        await uow.employees.add(emp2)
        await uow.employees.add(inactive_emp)
        await uow.commit()

    mark_all_uc = MarkAllPresentUseCase(sqlalchemy_uow)
    cmd = MarkAllPresentCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=ATTENDANCE_DATE,
    )

    results = await mark_all_uc.execute(cmd)

    # Only the 2 active employees get attendance
    assert len(results) == 2
    assert all(r.status == AttendanceStatus.PRESENT for r in results)
    assert all(r.overtime_hours == Decimal("0") for r in results)

    # Inactive employee should NOT have attendance
    async with sqlalchemy_uow as uow:
        inactive_att = await uow.attendance.get_by_employee_and_date(
            business_id=business.id,
            employee_id=inactive_emp.id,
            date_=ATTENDANCE_DATE,
        )
        assert inactive_att is None
