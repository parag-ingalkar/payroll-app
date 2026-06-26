from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.value_objects import SalaryBasis, WageType
from app.core.db import Base
from app.employees.domain.entities import Employee

if TYPE_CHECKING:
    # from app.attendance.infrastructure.orm import AttendanceModel
    from app.businesses.infrastructure.models import BusinessModel


class EmployeeModel(Base):
    __tablename__ = "employees"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    business_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    wage_type: Mapped[WageType] = mapped_column(
        Enum(
            WageType,
            name="wage_type",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    salary_basis: Mapped[SalaryBasis] = mapped_column(
        Enum(
            SalaryBasis,
            name="salary_basis",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    wage_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    working_hours_per_day: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    overtime_multiplier: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    business: Mapped["BusinessModel"] = relationship(back_populates="employees")

    # attendance: Mapped[list["AttendanceModel"]] = relationship(
    #     back_populates="employee",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True,
    # )

    @classmethod
    def from_entity(cls, employee: Employee) -> "EmployeeModel":
        return cls(
            id=employee.id,
            business_id=employee.business_id,
            name=employee.name,
            designation=employee.designation,
            wage_type=employee.wage_type,
            salary_basis=employee.salary_basis,
            wage_rate=employee.wage_rate,
            working_hours_per_day=employee.working_hours_per_day,
            overtime_multiplier=employee.overtime_multiplier,
            is_active=employee.is_active,
        )

    def to_entity(self) -> Employee:
        return Employee(
            id=self.id,
            business_id=self.business_id,
            name=self.name,
            designation=self.designation,
            wage_type=self.wage_type,
            salary_basis=self.salary_basis,
            wage_rate=self.wage_rate,
            working_hours_per_day=self.working_hours_per_day,
            overtime_multiplier=self.overtime_multiplier,
            is_active=self.is_active,
        )
