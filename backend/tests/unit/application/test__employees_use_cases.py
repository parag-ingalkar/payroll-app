# tests/unit/application/test__employees_use_cases.py
from decimal import Decimal
from uuid import uuid4

import pytest

from app.business.domain.entities import WageType
from app.business.domain.exceptions import BusinessNotFoundError
from app.business.domain.value_objects import SalaryBasis
from app.employees.application.commands import (
    ActivateEmployeeCommand,
    CreateEmployeeCommand,
    DeactivateEmployeeCommand,
    DeleteEmployeeCommand,
    GetEmployeeByIdCommand,
    ListEmployeesCommand,
    UpdateEmployeeCommand,
)
from app.employees.application.use_cases import (
    ActivateEmployeeUseCase,
    CreateEmployeeUseCase,
    DeactivateEmployeeUseCase,
    DeleteEmployeeUseCase,
    GetEmployeeByIdUseCase,
    ListEmployeesUseCase,
    UpdateEmployeeUseCase,
)
from app.employees.domain.entities import Employee
from app.employees.domain.exceptions import EmployeeNotFoundError


def _create_cmd(business_id, owner_id, **overrides) -> CreateEmployeeCommand:
    return CreateEmployeeCommand(
        id=overrides.get("id", uuid4()),
        business_id=overrides.get("business_id", business_id),
        owner_id=overrides.get("owner_id", owner_id),
        name=overrides.get("name", "Jane Smith"),
        designation=overrides.get("designation", "Analyst"),
        wage_type=overrides.get("wage_type", None),  # should use business default
        salary_basis=overrides.get("salary_basis", None),  # should use business default
        wage_rate=overrides.get("wage_rate", Decimal("40000.00")),
        working_hours_per_day=overrides.get(
            "working_hours_per_day", None
        ),  # should use business default
        overtime_multiplier=overrides.get(
            "overtime_multiplier", None
        ),  # should use business default
    )


@pytest.mark.asyncio
async def test__create_employee_use_case(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = CreateEmployeeUseCase(uow=in_memory_uow)
    cmd = _create_cmd(business.id, owner_id)

    employee = await use_case.execute(cmd)

    assert employee.name == "Jane Smith"
    assert employee.designation == "Analyst"
    assert employee.wage_rate == Decimal("40000.00")
    assert employee.is_active is True
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__create_employee_uses_business_defaults(
    business_defaults,
    in_memory_uow,
):
    """When wage_type, salary_basis, working_hours_per_day, overtime_multiplier are None,
    the business defaults should be applied."""
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = CreateEmployeeUseCase(uow=in_memory_uow)
    cmd = _create_cmd(
        business.id,
        owner_id,
        wage_type=None,
        salary_basis=None,
        working_hours_per_day=None,
        overtime_multiplier=None,
    )

    employee = await use_case.execute(cmd)

    assert employee.wage_type == business_defaults["default_wage_type"]
    assert employee.salary_basis == business_defaults["default_salary_basis"]
    assert (
        employee.working_hours_per_day
        == business_defaults["default_working_hours_per_day"]
    )
    assert (
        employee.overtime_multiplier == business_defaults["default_overtime_multiplier"]
    )


@pytest.mark.asyncio
async def test__create_employee_overrides_business_defaults(
    business_defaults,
    in_memory_uow,
):
    """Explicitly provided fields should NOT be replaced by business defaults."""
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = CreateEmployeeUseCase(uow=in_memory_uow)
    cmd = _create_cmd(
        business.id,
        owner_id,
        wage_type=WageType.DAILY,
        working_hours_per_day=Decimal("9.0"),
        overtime_multiplier=Decimal("2.0"),
    )

    employee = await use_case.execute(cmd)

    assert employee.wage_type == WageType.DAILY
    assert employee.working_hours_per_day == Decimal("9.0")
    assert employee.overtime_multiplier == Decimal("2.0")


@pytest.mark.asyncio
async def test__create_employee_wrong_owner_raises_error(
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]

    use_case = CreateEmployeeUseCase(uow=in_memory_uow)
    cmd = _create_cmd(business.id, "wrong-owner")

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__list_employees_use_case(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = ListEmployeesUseCase(uow=in_memory_uow)
    cmd = ListEmployeesCommand(
        business_id=business.id,
        owner_id=owner_id,
    )

    employees = await use_case.execute(cmd)

    assert len(employees) == 1
    assert employees[0].name == "John Doe"


@pytest.mark.asyncio
async def test__list_employees_filter_by_active(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]

    inactive_employee = Employee.create(
        id=uuid4(),
        business_id=business.id,
        name="Inactive Person",
        designation=None,
        wage_type=WageType.DAILY,
        salary_basis=SalaryBasis.WORKING_26_DAYS,
        wage_rate=Decimal("800.00"),
        working_hours_per_day=Decimal("8.0"),
        overtime_multiplier=Decimal("1.5"),
    )
    inactive_employee.deactivate()
    await in_memory_uow.employees.add(inactive_employee)

    use_case = ListEmployeesUseCase(uow=in_memory_uow)

    active_employees = await use_case.execute(
        ListEmployeesCommand(business_id=business.id, owner_id=owner_id, is_active=True)
    )
    assert len(active_employees) == 1
    assert all(e.is_active for e in active_employees)

    inactive_employees = await use_case.execute(
        ListEmployeesCommand(
            business_id=business.id, owner_id=owner_id, is_active=False
        )
    )
    assert len(inactive_employees) == 1
    assert not any(e.is_active for e in inactive_employees)


@pytest.mark.asyncio
async def test__get_employee_by_id_use_case(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]
    employee = in_memory_uow.employees._items[0]

    use_case = GetEmployeeByIdUseCase(uow=in_memory_uow)
    cmd = GetEmployeeByIdCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
    )

    fetched = await use_case.execute(cmd)

    assert fetched.id == employee.id
    assert fetched.name == "John Doe"


@pytest.mark.asyncio
async def test__get_employee_by_id_not_found(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = GetEmployeeByIdUseCase(uow=in_memory_uow)
    cmd = GetEmployeeByIdCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=uuid4(),
    )

    with pytest.raises(EmployeeNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__update_employee_name(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]
    employee = in_memory_uow.employees._items[0]

    use_case = UpdateEmployeeUseCase(uow=in_memory_uow)
    cmd = UpdateEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        fields_to_update=frozenset({"name"}),
        name="John D.",
    )

    updated = await use_case.execute(cmd)

    assert updated.name == "John D."
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__update_employee_clears_designation(
    business_defaults,
    in_memory_uow,
):
    """Explicitly sending designation=null should clear it."""
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]
    employee = in_memory_uow.employees._items[0]

    assert employee.designation is not None  # seeded with "Engineer"

    use_case = UpdateEmployeeUseCase(uow=in_memory_uow)
    cmd = UpdateEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        fields_to_update=frozenset({"designation"}),
        designation=None,
    )

    updated = await use_case.execute(cmd)
    assert updated.designation is None


# Test removed: is_active should not be updateable via PATCH.
# Use dedicated activate/deactivate endpoints instead.


@pytest.mark.asyncio
async def test__update_employee_wage_fields(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]
    employee = in_memory_uow.employees._items[0]

    use_case = UpdateEmployeeUseCase(uow=in_memory_uow)
    cmd = UpdateEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
        fields_to_update=frozenset(
            {"wage_type", "wage_rate", "working_hours_per_day", "overtime_multiplier"}
        ),
        wage_type=WageType.DAILY,
        wage_rate=Decimal("2000.00"),
        working_hours_per_day=Decimal("9.0"),
        overtime_multiplier=Decimal("2.0"),
    )

    updated = await use_case.execute(cmd)

    assert updated.wage_type == WageType.DAILY
    assert updated.wage_rate == Decimal("2000.00")
    assert updated.working_hours_per_day == Decimal("9.0")
    assert updated.overtime_multiplier == Decimal("2.0")


@pytest.mark.asyncio
async def test__update_employee_not_found_raises_error(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = UpdateEmployeeUseCase(uow=in_memory_uow)
    cmd = UpdateEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=uuid4(),
        fields_to_update=frozenset({"name"}),
        name="Ghost",
    )

    with pytest.raises(EmployeeNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__delete_employee_use_case(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]
    employee = in_memory_uow.employees._items[0]

    use_case = DeleteEmployeeUseCase(uow=in_memory_uow)
    cmd = DeleteEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
    )

    await use_case.execute(cmd)

    assert in_memory_uow.committed is True
    remaining = await in_memory_uow.employees.list_by_business(business_id=business.id)
    assert len(remaining) == 0


@pytest.mark.asyncio
async def test__delete_employee_not_found_raises_error(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = DeleteEmployeeUseCase(uow=in_memory_uow)
    cmd = DeleteEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=uuid4(),
    )

    with pytest.raises(EmployeeNotFoundError):
        await use_case.execute(cmd)


# Authorization Tests


@pytest.mark.asyncio
async def test__list_employees_wrong_owner_raises_error(
    in_memory_uow,
):
    """Listing employees with wrong owner_id should raise BusinessNotFoundError."""
    business = in_memory_uow.businesses._items[0]

    use_case = ListEmployeesUseCase(uow=in_memory_uow)
    cmd = ListEmployeesCommand(
        business_id=business.id,
        owner_id="wrong-owner-id",
    )

    with pytest.raises(BusinessNotFoundError) as exc_info:
        await use_case.execute(cmd)

    assert "not found for owner" in str(exc_info.value)


@pytest.mark.asyncio
async def test__get_employee_by_id_wrong_owner_raises_error(
    in_memory_uow,
):
    """Getting an employee by id with wrong owner_id should raise BusinessNotFoundError."""
    business = in_memory_uow.businesses._items[0]
    employee = in_memory_uow.employees._items[0]

    use_case = GetEmployeeByIdUseCase(uow=in_memory_uow)
    cmd = GetEmployeeByIdCommand(
        business_id=business.id,
        owner_id="wrong-owner-id",
        employee_id=employee.id,
    )

    with pytest.raises(BusinessNotFoundError) as exc_info:
        await use_case.execute(cmd)

    assert "not found for owner" in str(exc_info.value)


@pytest.mark.asyncio
async def test__update_employee_wrong_owner_raises_error(
    in_memory_uow,
):
    """Updating an employee with wrong owner_id should raise BusinessNotFoundError."""
    business = in_memory_uow.businesses._items[0]
    employee = in_memory_uow.employees._items[0]

    use_case = UpdateEmployeeUseCase(uow=in_memory_uow)
    cmd = UpdateEmployeeCommand(
        business_id=business.id,
        owner_id="wrong-owner-id",
        employee_id=employee.id,
        fields_to_update=frozenset({"name"}),
        name="Should Not Work",
    )

    with pytest.raises(BusinessNotFoundError) as exc_info:
        await use_case.execute(cmd)

    assert "not found for owner" in str(exc_info.value)
    assert in_memory_uow.committed is False


@pytest.mark.asyncio
async def test__delete_employee_wrong_owner_raises_error(
    in_memory_uow,
):
    """Deleting an employee with wrong owner_id should raise BusinessNotFoundError."""
    business = in_memory_uow.businesses._items[0]
    employee = in_memory_uow.employees._items[0]

    use_case = DeleteEmployeeUseCase(uow=in_memory_uow)
    cmd = DeleteEmployeeCommand(
        business_id=business.id,
        owner_id="wrong-owner-id",
        employee_id=employee.id,
    )

    with pytest.raises(BusinessNotFoundError) as exc_info:
        await use_case.execute(cmd)

    assert "not found for owner" in str(exc_info.value)
    assert in_memory_uow.committed is False


@pytest.mark.asyncio
async def test__deactivate_employee_happy_path(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]
    employee = in_memory_uow.employees._items[0]

    assert employee.is_active is True

    use_case = DeactivateEmployeeUseCase(uow=in_memory_uow)
    cmd = DeactivateEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
    )

    updated = await use_case.execute(cmd)

    assert updated.is_active is False
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__deactivate_employee_idempotent(
    business_defaults,
    in_memory_uow,
):
    """Deactivating an already inactive employee should be idempotent."""
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]
    employee = in_memory_uow.employees._items[0]

    employee.deactivate()
    assert employee.is_active is False

    use_case = DeactivateEmployeeUseCase(uow=in_memory_uow)
    cmd = DeactivateEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
    )

    updated = await use_case.execute(cmd)

    assert updated.is_active is False
    # Should not commit if already inactive (optimization)
    assert in_memory_uow.committed is False


@pytest.mark.asyncio
async def test__deactivate_employee_wrong_owner_raises_error(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    employee = in_memory_uow.employees._items[0]

    use_case = DeactivateEmployeeUseCase(uow=in_memory_uow)
    cmd = DeactivateEmployeeCommand(
        business_id=business.id,
        owner_id="wrong-owner",
        employee_id=employee.id,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__deactivate_employee_not_found_raises_error(
    business_defaults,
    in_memory_uow,
):
    from uuid import uuid4

    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = DeactivateEmployeeUseCase(uow=in_memory_uow)
    cmd = DeactivateEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=uuid4(),
    )

    with pytest.raises(EmployeeNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__activate_employee_happy_path(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]
    employee = in_memory_uow.employees._items[0]

    employee.deactivate()
    assert employee.is_active is False

    use_case = ActivateEmployeeUseCase(uow=in_memory_uow)
    cmd = ActivateEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
    )

    updated = await use_case.execute(cmd)

    assert updated.is_active is True
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__activate_employee_idempotent(
    business_defaults,
    in_memory_uow,
):
    """Activating an already active employee should be idempotent."""
    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]
    employee = in_memory_uow.employees._items[0]

    assert employee.is_active is True

    use_case = ActivateEmployeeUseCase(uow=in_memory_uow)
    cmd = ActivateEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=employee.id,
    )

    updated = await use_case.execute(cmd)

    assert updated.is_active is True
    # Should not commit if already active (optimization)
    assert in_memory_uow.committed is False


@pytest.mark.asyncio
async def test__activate_employee_wrong_owner_raises_error(
    business_defaults,
    in_memory_uow,
):
    business = in_memory_uow.businesses._items[0]
    employee = in_memory_uow.employees._items[0]

    use_case = ActivateEmployeeUseCase(uow=in_memory_uow)
    cmd = ActivateEmployeeCommand(
        business_id=business.id,
        owner_id="wrong-owner",
        employee_id=employee.id,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__activate_employee_not_found_raises_error(
    business_defaults,
    in_memory_uow,
):
    from uuid import uuid4

    business = in_memory_uow.businesses._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = ActivateEmployeeUseCase(uow=in_memory_uow)
    cmd = ActivateEmployeeCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=uuid4(),
    )

    with pytest.raises(EmployeeNotFoundError):
        await use_case.execute(cmd)
