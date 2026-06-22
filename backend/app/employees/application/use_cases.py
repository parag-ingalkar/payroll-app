from collections.abc import Sequence
from dataclasses import dataclass

from app.business.domain.exceptions import BusinessNotFoundError
from app.core.uow import UnitOfWorkPort
from app.employees.application.commands import (
    CreateEmployeeCommand,
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
                id=cmd.id,
                business_id=cmd.business_id,
                name=cmd.name,
                designation=cmd.designation,
                wage_type=wage_type,
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
                    business_id=str(cmd.business_id),
                    employee_id=str(cmd.employee_id),
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
                    business_id=str(cmd.business_id),
                    employee_id=str(cmd.employee_id),
                )

            if "name" in cmd.fields_to_update and cmd.name is not None:
                employee.rename(cmd.name)

            if "designation" in cmd.fields_to_update:
                # cmd.designation may be None to clear the field
                employee.designation = cmd.designation

            if "wage_type" in cmd.fields_to_update and cmd.wage_type is not None:
                employee.wage_type = cmd.wage_type

            if "wage_rate" in cmd.fields_to_update and cmd.wage_rate is not None:
                employee.wage_rate = cmd.wage_rate

            if (
                "working_hours_per_day" in cmd.fields_to_update
                and cmd.working_hours_per_day is not None
            ):
                employee.working_hours_per_day = cmd.working_hours_per_day

            if (
                "overtime_multiplier" in cmd.fields_to_update
                and cmd.overtime_multiplier is not None
            ):
                employee.overtime_multiplier = cmd.overtime_multiplier

            if "is_active" in cmd.fields_to_update and cmd.is_active is not None:
                if cmd.is_active:
                    employee.activate()
                else:
                    employee.deactivate()

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
                    business_id=str(cmd.business_id),
                    employee_id=str(cmd.employee_id),
                )

            await uow.employees.delete(employee)
            await uow.commit()
