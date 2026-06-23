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

# ── shared factory helpers (no pytest fixture, just callables) ─────────────────


async def _api_create_business(api_client, name: str = "Test Business") -> str:
    resp = await api_client.post(
        "/businesses",
        json={
            "name": name,
            "default_wage_type": "monthly",
            "default_salary_basis": "working_26_days",
            "default_working_hours_per_day": "8.0",
            "default_overtime_multiplier": "1.5",
            "payroll_start_day": 1,
            "weekly_off_rules": [],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _api_create_employee(api_client, business_id: str) -> str:
    resp = await api_client.post(
        f"/businesses/{business_id}/employees",
        json={
            "name": "Test Worker",
            "designation": "Engineer",
            "wage_type": "monthly",
            "salary_basis": "working_26_days",
            "wage_rate": "30000.00",
            "working_hours_per_day": "8.0",
            "overtime_multiplier": "1.5",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _api_seed_attendance(
    api_client, business_id: str, employee_id: str, year: int, month: int, days: int
):
    for d in range(1, days + 1):
        resp = await api_client.post(
            f"/businesses/{business_id}/attendance",
            json={
                "employee_id": employee_id,
                "date": date(year, month, d).isoformat(),
                "status": "present",
            },
        )
        assert resp.status_code == 201, resp.text


# ── fixtures used by sqlalchemy tests (direct UoW, no api_client) ─────────────


@pytest.fixture
async def create_business_via_api(api_client, business_defaults):
    """Returns a factory function that creates a business via the API."""

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
        assert resp.status_code == 201, resp.text
        return UUID(resp.json()["id"])

    return _create


@pytest.fixture
async def add_business_in_db(
    sqlalchemy_uow: SqlAlchemyUnitOfWork,
    business_defaults: dict,
) -> Business:
    # Use the already-open UoW directly — no nested `async with`
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
    # Use the already-open UoW directly — no nested `async with`
    holiday = Holiday.create(
        business_id=add_business_in_db.id,
        date_=date(2026, 1, 1),
        name="New Year's Day",
    )
    await sqlalchemy_uow.holidays.add(holiday)
    await sqlalchemy_uow.commit()


@pytest.fixture
async def add_employee_in_db(
    sqlalchemy_uow: SqlAlchemyUnitOfWork,
    add_business_in_db: Business,
) -> Employee:
    # Use the already-open UoW directly — no nested `async with`
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
    await sqlalchemy_uow.employees.add(employee)
    await sqlalchemy_uow.commit()
    return employee


@pytest.fixture
async def add_attendance_in_db(
    sqlalchemy_uow: SqlAlchemyUnitOfWork,
    add_employee_in_db: Employee,
) -> Attendance:
    # Use the already-open UoW directly — no nested `async with`
    attendance = Attendance.create(
        id=uuid4(),
        business_id=add_employee_in_db.business_id,
        employee_id=add_employee_in_db.id,
        date=date(2026, 6, 10),
        status=AttendanceStatus.PRESENT,
    )
    await sqlalchemy_uow.attendance.add(attendance)
    await sqlalchemy_uow.commit()
    return attendance


# ── payroll-specific fixtures (api_client only) ────────────────────────────────


@pytest.fixture
async def seeded_business(api_client) -> str:
    """Creates a business via API and returns its id (str)."""
    return await _api_create_business(api_client, f"Payroll Biz {uuid4().hex[:6]}")


@pytest.fixture
async def seeded_business_with_employee(api_client, seeded_business) -> dict:
    """Creates a business + employee via API. Returns {"business_id", "employee_id"}."""
    employee_id = await _api_create_employee(api_client, seeded_business)
    return {"business_id": seeded_business, "employee_id": employee_id}


@pytest.fixture
async def seeded_payroll_run(api_client, seeded_business_with_employee) -> dict:
    """
    Seeds a business, employee, 26 days of attendance for Jan 2026,
    runs payroll, and returns the full context dict:
    {"business_id", "employee_id", "run_id", "year", "month"}.
    """
    business_id = seeded_business_with_employee["business_id"]
    employee_id = seeded_business_with_employee["employee_id"]

    await _api_seed_attendance(api_client, business_id, employee_id, 2026, 1, 26)

    resp = await api_client.post(
        f"/businesses/{business_id}/payroll/run",
        json={"year": 2026, "month": 1},
    )
    assert resp.status_code == 201, resp.text

    return {
        "business_id": business_id,
        "employee_id": employee_id,
        "run_id": resp.json()["id"],
        "year": 2026,
        "month": 1,
    }
