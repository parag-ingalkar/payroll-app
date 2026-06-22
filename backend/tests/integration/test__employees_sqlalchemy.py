# tests/integration/test__employees_sqlalchemy.py
from decimal import Decimal
from uuid import uuid4

import pytest

from app.business.domain.entities import WageType
from app.employees.application.commands import (
    CreateEmployeeCommand,
    DeleteEmployeeCommand,
    GetEmployeeByIdCommand,
    ListEmployeesCommand,
    UpdateEmployeeCommand,
)
from app.employees.application.use_cases import (
    CreateEmployeeUseCase,
    DeleteEmployeeUseCase,
    GetEmployeeByIdUseCase,
    ListEmployeesUseCase,
    UpdateEmployeeUseCase,
)
from app.employees.domain.entities import Employee
from app.employees.domain.exceptions import EmployeeNotFoundError


@pytest.mark.asyncio
async def test__create_employee(
    sqlalchemy_uow,
    add_business_in_db,
    business_defaults,
):
    business = add_business_in_db
    owner_id = business_defaults["owner_id"]

    create_uc = CreateEmployeeUseCase(sqlalchemy_uow)
    cmd = CreateEmployeeCommand(
        id=uuid4(),
        business_id=business.id,
        owner_id=owner_id,
        name="John Doe",
        designation="Engineer",
        wage_type=WageType.MONTHLY,
        wage_rate=Decimal("50000.00"),
        working_hours_per_day=Decimal("8.0"),
        overtime_multiplier=Decimal("1.5"),
    )

    created = await create_uc.execute(cmd)

    assert created.name == "John Doe"
    assert created.designation == "Engineer"
    assert created.wage_type == WageType.MONTHLY
    assert created.is_active is True

    async with sqlalchemy_uow as uow:
        reloaded = await uow.employees.get_by_business_and_id(
            business_id=created.business_id,
            employee_id=created.id,
        )
        assert reloaded is not None
        assert reloaded.id == created.id
        assert reloaded.name == "John Doe"
        assert reloaded.designation == "Engineer"


@pytest.mark.asyncio
async def test__create_employee_uses_business_defaults(
    sqlalchemy_uow,
    add_business_in_db,
    business_defaults,
):
    business = add_business_in_db
    owner_id = business_defaults["owner_id"]

    create_uc = CreateEmployeeUseCase(sqlalchemy_uow)
    cmd = CreateEmployeeCommand(
        id=uuid4(),
        business_id=business.id,
        owner_id=owner_id,
        name="Alice",
        designation=None,
        wage_type=None,
        wage_rate=Decimal("30000.00"),
        working_hours_per_day=None,
        overtime_multiplier=None,
    )

    created = await create_uc.execute(cmd)

    assert created.wage_type == business_defaults["default_wage_type"]
    assert (
        created.working_hours_per_day
        == business_defaults["default_working_hours_per_day"]
    )
    assert (
        created.overtime_multiplier == business_defaults["default_overtime_multiplier"]
    )


@pytest.mark.asyncio
async def test__list_employees(
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
        )
        emp2 = Employee.create(
            id=uuid4(),
            business_id=business.id,
            name="Bob",
            designation="Manager",
            wage_type=WageType.HOURLY,
            wage_rate=Decimal("100.00"),
            working_hours_per_day=Decimal("8.0"),
            overtime_multiplier=Decimal("2.0"),
        )
        await uow.employees.add(emp1)
        await uow.employees.add(emp2)
        await uow.commit()

    list_uc = ListEmployeesUseCase(sqlalchemy_uow)
    cmd = ListEmployeesCommand(business_id=business.id, owner_id=owner_id)

    employees = await list_uc.execute(cmd)

    assert len(employees) == 2
    assert employees[0].name == "Alice"
    assert employees[1].name == "Bob"


@pytest.mark.asyncio
async def test__get_employee_by_id(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    get_uc = GetEmployeeByIdUseCase(sqlalchemy_uow)
    cmd = GetEmployeeByIdCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
    )

    fetched = await get_uc.execute(cmd)

    assert fetched.id == employee.id
    assert fetched.name == "John Doe"
    assert fetched.designation == "Engineer"


@pytest.mark.asyncio
async def test__update_employee_name(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    update_uc = UpdateEmployeeUseCase(sqlalchemy_uow)
    cmd = UpdateEmployeeCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
        fields_to_update=frozenset({"name"}),
        name="John D.",
    )

    updated = await update_uc.execute(cmd)
    assert updated.name == "John D."

    async with sqlalchemy_uow as uow:
        reloaded = await uow.employees.get_by_business_and_id(
            business_id=employee.business_id,
            employee_id=employee.id,
        )
        assert reloaded is not None
        assert reloaded.name == "John D."


@pytest.mark.asyncio
async def test__update_employee_clears_designation(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    update_uc = UpdateEmployeeUseCase(sqlalchemy_uow)
    cmd = UpdateEmployeeCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
        fields_to_update=frozenset({"designation"}),
        designation=None,
    )

    updated = await update_uc.execute(cmd)
    assert updated.designation is None

    async with sqlalchemy_uow as uow:
        reloaded = await uow.employees.get_by_business_and_id(
            business_id=employee.business_id,
            employee_id=employee.id,
        )
        assert reloaded is not None
        assert reloaded.designation is None


@pytest.mark.asyncio
async def test__update_employee_deactivate(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    update_uc = UpdateEmployeeUseCase(sqlalchemy_uow)
    cmd = UpdateEmployeeCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
        fields_to_update=frozenset({"is_active"}),
        is_active=False,
    )

    updated = await update_uc.execute(cmd)
    assert updated.is_active is False

    async with sqlalchemy_uow as uow:
        reloaded = await uow.employees.get_by_business_and_id(
            business_id=employee.business_id,
            employee_id=employee.id,
        )
        assert reloaded is not None
        assert reloaded.is_active is False


@pytest.mark.asyncio
async def test__delete_employee(
    sqlalchemy_uow,
    add_employee_in_db,
    business_defaults,
):
    employee = add_employee_in_db
    owner_id = business_defaults["owner_id"]

    delete_uc = DeleteEmployeeUseCase(sqlalchemy_uow)
    cmd = DeleteEmployeeCommand(
        business_id=employee.business_id,
        owner_id=owner_id,
        employee_id=employee.id,
    )

    await delete_uc.execute(cmd)

    async with sqlalchemy_uow as uow:
        reloaded = await uow.employees.get_by_business_and_id(
            business_id=employee.business_id,
            employee_id=employee.id,
        )
        assert reloaded is None


@pytest.mark.asyncio
async def test__get_employee_not_found_raises_error(
    sqlalchemy_uow,
    add_business_in_db,
    business_defaults,
):
    business = add_business_in_db
    owner_id = business_defaults["owner_id"]

    get_uc = GetEmployeeByIdUseCase(sqlalchemy_uow)
    cmd = GetEmployeeByIdCommand(
        business_id=business.id,
        owner_id=owner_id,
        employee_id=uuid4(),
    )

    with pytest.raises(EmployeeNotFoundError):
        await get_uc.execute(cmd)
