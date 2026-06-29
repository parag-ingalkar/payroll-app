from collections.abc import Sequence
from dataclasses import dataclass

from app.businesses.domain.exceptions import BusinessNotFoundError
from app.core.uow import UnitOfWorkPort
from app.employees.application.commands import (
    ActivateEmployeeCommand,
    CreateEmployeeCommand,
    DeactivateEmployeeCommand,
    DeleteEmployeeCommand,
    GetEmployeeByIdCommand,
    ListEmployeesCommand,
    UpdateEmployeeCommand,
)
from app.employees.domain.entities import Employee
from app.employees.domain.exceptions import EmployeeNotFoundError


@dataclass
class CreateEmployeeUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: CreateEmployeeCommand) -> Employee:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            # Apply business defaults for any omitted wage fields
            wage_type = (
                cmd.wage_type
                if cmd.wage_type is not None
                else business.default_wage_type
            )
            salary_basis = (
                cmd.salary_basis
                if cmd.salary_basis is not None
                else business.default_salary_basis
            )
            working_hours_per_day = (
                cmd.working_hours_per_day
                if cmd.working_hours_per_day is not None
                else business.default_working_hours_per_day
            )
            overtime_multiplier = (
                cmd.overtime_multiplier
                if cmd.overtime_multiplier is not None
                else business.default_overtime_multiplier
            )

            employee = Employee.create(
                business_id=cmd.business_id,
                name=cmd.name,
                designation=cmd.designation,
                wage_type=wage_type,
                salary_basis=salary_basis,
                wage_rate=cmd.wage_rate,
                working_hours_per_day=working_hours_per_day,
                overtime_multiplier=overtime_multiplier,
            )
            await uow.employees.add(employee)
            await uow.commit()
            return employee


@dataclass
class ListEmployeesUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: ListEmployeesCommand) -> Sequence[Employee]:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            employees = await uow.employees.list_by_business(
                business_id=cmd.business_id, is_active=cmd.is_active
            )
            return sorted(employees, key=lambda e: e.name)


@dataclass
class GetEmployeeByIdUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: GetEmployeeByIdCommand) -> Employee:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            employee = await uow.employees.get_by_business_and_id(
                business_id=cmd.business_id, employee_id=cmd.employee_id
            )
            if not employee:
                raise EmployeeNotFoundError(
                    f"Employee with id {cmd.employee_id} not found in business {cmd.business_id}."
                )
            return employee


@dataclass
class UpdateEmployeeUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: UpdateEmployeeCommand) -> Employee:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            employee = await uow.employees.get_by_business_and_id(
                business_id=cmd.business_id, employee_id=cmd.employee_id
            )
            if not employee:
                raise EmployeeNotFoundError(
                    f"Employee with id {cmd.employee_id} not found in business {cmd.business_id}."
                )

            kwargs = {}
            if "name" in cmd.fields_to_update:
                kwargs["name"] = cmd.name
            if "designation" in cmd.fields_to_update:
                kwargs["designation"] = cmd.designation
            if "wage_type" in cmd.fields_to_update:
                kwargs["wage_type"] = cmd.wage_type
            if "salary_basis" in cmd.fields_to_update:
                kwargs["salary_basis"] = cmd.salary_basis
            if "wage_rate" in cmd.fields_to_update:
                kwargs["wage_rate"] = cmd.wage_rate
            if "working_hours_per_day" in cmd.fields_to_update:
                kwargs["working_hours_per_day"] = cmd.working_hours_per_day
            if "overtime_multiplier" in cmd.fields_to_update:
                kwargs["overtime_multiplier"] = cmd.overtime_multiplier

            employee.update_details(**kwargs)

            await uow.employees.update(employee)
            await uow.commit()
            return employee


@dataclass
class DeactivateEmployeeUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: DeactivateEmployeeCommand) -> Employee:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            employee = await uow.employees.get_by_business_and_id(
                business_id=cmd.business_id, employee_id=cmd.employee_id
            )
            if not employee:
                raise EmployeeNotFoundError(
                    f"Employee with id {cmd.employee_id} not found in business {cmd.business_id}."
                )

            if employee.is_active:
                employee.deactivate()
                await uow.employees.update(employee)
                await uow.commit()
            return employee


@dataclass
class ActivateEmployeeUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: ActivateEmployeeCommand) -> Employee:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            employee = await uow.employees.get_by_business_and_id(
                business_id=cmd.business_id, employee_id=cmd.employee_id
            )
            if not employee:
                raise EmployeeNotFoundError(
                    f"Employee with id {cmd.employee_id} not found in business {cmd.business_id}."
                )

            if not employee.is_active:
                employee.activate()
                await uow.employees.update(employee)
                await uow.commit()
            return employee


@dataclass
class DeleteEmployeeUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: DeleteEmployeeCommand) -> None:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            employee = await uow.employees.get_by_business_and_id(
                business_id=cmd.business_id, employee_id=cmd.employee_id
            )
            if not employee:
                raise EmployeeNotFoundError(
                    f"Employee with id {cmd.employee_id} not found in business {cmd.business_id}."
                )

            await uow.employees.delete(employee)
            await uow.commit()
