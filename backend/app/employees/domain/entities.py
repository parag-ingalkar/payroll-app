from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.business.domain.entities import WageType
from app.employees.domain.exceptions import InvalidEmployeeNameError


@dataclass
class Employee:
    id: UUID
    business_id: UUID
    name: str
    designation: str | None
    wage_type: WageType
    wage_rate: Decimal
    working_hours_per_day: Decimal
    overtime_multiplier: Decimal
    is_active: bool

    @classmethod
    def create(
        cls,
        id: UUID,
        business_id: UUID,
        name: str,
        designation: str | None,
        wage_type: WageType,
        wage_rate: Decimal,
        working_hours_per_day: Decimal,
        overtime_multiplier: Decimal,
    ) -> "Employee":
        stripped_name = name.strip()
        if not stripped_name:
            raise InvalidEmployeeNameError("Employee name cannot be empty.")
        stripped_designation = designation.strip() if designation else None
        return cls(
            id=id,
            business_id=business_id,
            name=stripped_name,
            designation=stripped_designation or None,
            wage_type=wage_type,
            wage_rate=wage_rate,
            working_hours_per_day=working_hours_per_day,
            overtime_multiplier=overtime_multiplier,
            is_active=True,
        )

    def rename(self, new_name: str) -> None:
        stripped = new_name.strip()
        if not stripped:
            raise InvalidEmployeeNameError("Employee name cannot be empty.")
        self.name = stripped

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False
