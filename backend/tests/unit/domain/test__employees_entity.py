# tests/unit/domain/test__employees_entity.py
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.business.domain.entities import WageType
from app.business.domain.value_objects import SalaryBasis
from app.employees.domain.entities import Employee
from app.employees.domain.exceptions import InvalidEmployeeNameError

BUSINESS_ID = UUID("12345678-1234-5678-1234-567812345678")


def _make_employee(**overrides) -> Employee:
    return Employee.create(
        id=overrides.get("id", uuid4()),
        business_id=overrides.get("business_id", BUSINESS_ID),
        name=overrides.get("name", "John Doe"),
        designation=overrides.get("designation", "Engineer"),
        wage_type=overrides.get("wage_type", WageType.MONTHLY),
        salary_basis=overrides.get("salary_basis", SalaryBasis.WORKING_26_DAYS),
        wage_rate=overrides.get("wage_rate", Decimal("50000.00")),
        working_hours_per_day=overrides.get("working_hours_per_day", Decimal("8.0")),
        overtime_multiplier=overrides.get("overtime_multiplier", Decimal("1.5")),
    )


def test__create_employee_with_valid_fields():
    employee = _make_employee()
    assert employee.name == "John Doe"
    assert employee.designation == "Engineer"
    assert employee.wage_type == WageType.MONTHLY
    assert employee.wage_rate == Decimal("50000.00")
    assert employee.working_hours_per_day == Decimal("8.0")
    assert employee.overtime_multiplier == Decimal("1.5")
    assert employee.is_active is True
    assert employee.business_id == BUSINESS_ID


def test__create_employee_strips_trailing_whitespace_from_name():
    employee = _make_employee(name="  John Doe  ")
    assert employee.name == "John Doe"


def test__create_employee_with_none_designation():
    employee = _make_employee(designation=None)
    assert employee.designation is None


def test__create_employee_strips_designation():
    employee = _make_employee(designation="  Manager  ")
    assert employee.designation == "Manager"


def test__create_employee_with_empty_designation_becomes_none():
    employee = _make_employee(designation="   ")
    assert employee.designation is None


def test__create_employee_with_empty_name_raises_error():
    with pytest.raises(InvalidEmployeeNameError):
        _make_employee(name="   ")


def test__rename_employee_updates_name():
    employee = _make_employee()
    employee.rename("Jane Smith")
    assert employee.name == "Jane Smith"


def test__rename_employee_strips_whitespace():
    employee = _make_employee()
    employee.rename("  Jane Smith  ")
    assert employee.name == "Jane Smith"


def test__rename_employee_with_empty_name_raises_error():
    employee = _make_employee()
    with pytest.raises(InvalidEmployeeNameError):
        employee.rename("   ")


def test__deactivate_employee():
    employee = _make_employee()
    assert employee.is_active is True
    employee.deactivate()
    assert employee.is_active is False


def test__activate_employee():
    employee = _make_employee()
    employee.deactivate()
    employee.activate()
    assert employee.is_active is True
