# tests/integration/conftest.py
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.attendance.domain.entities import Attendance, AttendanceStatus
from app.business.domain.entities import Business, WageType
from app.business.domain.value_objects import SalaryBasis
from app.core.uow import SqlAlchemyUnitOfWork
from app.employees.domain.entities import Employee
from app.holidays.domain.entities import Holiday


@pytest.fixture
async def create_business_via_api(api_client, business_defaults):
    """Fixture that returns an async function to create a business via API."""

    async def _create() -> UUID:
        resp = await api_client.post(
            "/businesses",
            json={
                "name": business_defaults["name"],
                "default_wage_type": business_defaults["default_wage_type"].value,
                "default_salary_basis": business_defaults["default_salary_basis"].value,
                "default_working_hours_per_day": "8.0",
                "default_overtime_multiplier": "1.5",
                "payroll_start_day": 1,
                "weekly_off_rules": [],
            },
        )
        assert resp.status_code == 201
        return UUID(resp.json()["id"])

    return _create


@pytest.fixture
async def add_business_in_db(
    sqlalchemy_uow: SqlAlchemyUnitOfWork,
    business_defaults: dict,
) -> Business:
    business = Business.create(**business_defaults)
    business.id = UUID("12345678-1234-5678-1234-567812345678")
    await sqlalchemy_uow.businesses.add(business)
    await sqlalchemy_uow.commit()
    return business


@pytest.fixture
async def add_business_and_holiday_in_db(
    sqlalchemy_uow: SqlAlchemyUnitOfWork,
    add_business_in_db: Business,
) -> None:
    async with sqlalchemy_uow as uow:
        holiday = Holiday.create(
            business_id=add_business_in_db.id,
            date_=date(2026, 1, 1),
            name="New Year's Day",
        )
        await uow.holidays.add(holiday)
        await uow.commit()


@pytest.fixture
async def add_employee_in_db(
    sqlalchemy_uow: SqlAlchemyUnitOfWork,
    add_business_in_db: Business,
) -> Employee:
    employee = Employee.create(
        id=uuid4(),
        business_id=add_business_in_db.id,
        name="John Doe",
        designation="Engineer",
        wage_type=WageType.MONTHLY,
        salary_basis=SalaryBasis.WORKING_26_DAYS,
        wage_rate=Decimal("50000.00"),
        working_hours_per_day=Decimal("8.0"),
        overtime_multiplier=Decimal("1.5"),
    )
    async with sqlalchemy_uow as uow:
        await uow.employees.add(employee)
        await uow.commit()
    return employee


@pytest.fixture
async def add_attendance_in_db(
    sqlalchemy_uow: SqlAlchemyUnitOfWork,
    add_employee_in_db: Employee,
) -> Attendance:
    attendance = Attendance.create(
        id=uuid4(),
        business_id=add_employee_in_db.business_id,
        employee_id=add_employee_in_db.id,
        date=date(2026, 6, 10),
        status=AttendanceStatus.PRESENT,
    )
    async with sqlalchemy_uow as uow:
        await uow.attendance.add(attendance)
        await uow.commit()
    return attendance
