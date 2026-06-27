import uuid
from decimal import Decimal
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.shared.value_objects import AttendanceStatus
from app.attendances.domain.entities import Attendance

if TYPE_CHECKING:
    from app.businesses.infrastructure.models import BusinessModel
    from app.employees.infrastructure.models import EmployeeModel


class AttendanceModel(Base):
    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "employee_id",
            "date",
            name="uq_attendance_business_employee_date",
        ),
        CheckConstraint(
            "overtime_hours >= 0", name="check_overtime_hours_non_negative"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)  # YYYY-MM-DD format

    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, name="attendance_status_enum"), nullable=False
    )
    total_hours: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )
    overtime_hours: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False, default=Decimal("0")
    )
    marked_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    business: Mapped["BusinessModel"] = relationship(
        "BusinessModel", back_populates="attendances"
    )
    employee: Mapped["EmployeeModel"] = relationship(
        "EmployeeModel", back_populates="attendances"
    )

    @classmethod
    def from_entity(cls, attendance: Attendance) -> "AttendanceModel":
        return cls(
            id=attendance.id,
            business_id=attendance.business_id,
            employee_id=attendance.employee_id,
            date=attendance.date,
            status=attendance.status,
            total_hours=attendance.total_hours,
            overtime_hours=attendance.overtime_hours,
            marked_by=attendance.marked_by,
            notes=attendance.notes,
        )

    def to_entity(self) -> Attendance:
        return Attendance(
            business_id=self.business_id,
            employee_id=self.employee_id,
            date=self.date,
            status=self.status,
            total_hours=self.total_hours,
            overtime_hours=self.overtime_hours,
            marked_by=self.marked_by,
            notes=self.notes,
            id=self.id,
        )
