from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.shared.value_objects import SalaryBasis, WageType


@dataclass(slots=True)
class CreateEmployeeCommand:
    business_id: UUID
    owner_id: str
    id: UUID
    name: str
    designation: str | None
    wage_type: WageType | None
    salary_basis: SalaryBasis | None
    wage_rate: Decimal
    working_hours_per_day: Decimal | None
    overtime_multiplier: Decimal | None


@dataclass(slots=True)
class ListEmployeesCommand:
    business_id: UUID
    owner_id: str
    is_active: bool | None = None


@dataclass(slots=True)
class GetEmployeeByIdCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID


@dataclass(slots=True)
class UpdateEmployeeCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID
    fields_to_update: frozenset[str]
    name: str | None = None
    designation: str | None = None
    wage_type: WageType | None = None
    salary_basis: SalaryBasis | None = None
    wage_rate: Decimal | None = None
    working_hours_per_day: Decimal | None = None
    overtime_multiplier: Decimal | None = None


@dataclass(slots=True)
class DeactivateEmployeeCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID


@dataclass(slots=True)
class ActivateEmployeeCommand(DeactivateEmployeeCommand):
    pass


@dataclass(slots=True)
class DeleteEmployeeCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID