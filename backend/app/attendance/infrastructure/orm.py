from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Index, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.attendance.domain.entities import Attendance, AttendanceStatus
from app.core.db import Base

if TYPE_CHECKING:
    from app.business.infrastructure.orm import BusinessModel
    from app.employees.infrastructure.orm import EmployeeModel


class AttendanceModel(Base):
    __tablename__ = "attendance"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    business_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, name="attendance_status", native_enum=False),
        nullable=False,
    )
    overtime_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )

    business: Mapped["BusinessModel"] = relationship(back_populates="attendance")
    employee: Mapped["EmployeeModel"] = relationship(back_populates="attendance")

    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "employee_id",
            "date",
            name="uq_attendance_business_employee_date",
        ),
        Index("ix_attendance_business_date", "business_id", "date"),
    )

    @classmethod
    def from_entity(cls, attendance: Attendance) -> "AttendanceModel":
        return cls(
            id=attendance.id,
            business_id=attendance.business_id,
            employee_id=attendance.employee_id,
            date=attendance.date,
            status=attendance.status,
            overtime_hours=attendance.overtime_hours,
        )

    def to_entity(self) -> Attendance:
        return Attendance(
            id=self.id,
            business_id=self.business_id,
            employee_id=self.employee_id,
            date=self.date,
            status=self.status,
            overtime_hours=self.overtime_hours,
        )
