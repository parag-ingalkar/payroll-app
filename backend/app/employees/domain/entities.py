from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from app.shared.value_objects import SalaryBasis, WageType
from app.employees.domain.exceptions import InvalidEmployeeNameError


@dataclass
class Employee:
    business_id: UUID
    name: str
    designation: str | None
    wage_type: WageType
    salary_basis: SalaryBasis
    wage_rate: Decimal
    working_hours_per_day: Decimal
    overtime_multiplier: Decimal
    is_active: bool
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def create(
        cls,
        business_id: UUID,
        name: str,
        designation: str | None,
        wage_type: WageType,
        salary_basis: SalaryBasis,
        wage_rate: Decimal,
        working_hours_per_day: Decimal,
        overtime_multiplier: Decimal,
    ) -> "Employee":
        stripped_name = name.strip()
        if not stripped_name:
            raise InvalidEmployeeNameError("Employee name cannot be empty.")
        stripped_designation = designation.strip() if designation else None
        return cls(
            business_id=business_id,
            name=stripped_name,
            designation=stripped_designation or None,
            wage_type=wage_type,
            salary_basis=salary_basis,
            wage_rate=wage_rate,
            working_hours_per_day=working_hours_per_day,
            overtime_multiplier=overtime_multiplier,
            is_active=True,
        )

    def update_details(
        self,
        **kwargs,
    ) -> None:
        if "name" in kwargs:
            stripped_name = kwargs["name"].strip()
            if not stripped_name:
                raise InvalidEmployeeNameError("Employee name cannot be empty.")
            self.name = stripped_name
        if "designation" in kwargs:
            designation = kwargs["designation"]
            if designation is None:
                self.designation = None
            else:
                stripped_designation = designation.strip()
                self.designation = stripped_designation or None
        if "wage_type" in kwargs:
            self.wage_type = kwargs["wage_type"]
        if "salary_basis" in kwargs:
            self.salary_basis = kwargs["salary_basis"]
        if "wage_rate" in kwargs:
            self.wage_rate = kwargs["wage_rate"]
        if "working_hours_per_day" in kwargs:
            self.working_hours_per_day = kwargs["working_hours_per_day"]
        if "overtime_multiplier" in kwargs:
            self.overtime_multiplier = kwargs["overtime_multiplier"]

    def rename(self, new_name: str) -> None:
        self.update_details(name=new_name)

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False