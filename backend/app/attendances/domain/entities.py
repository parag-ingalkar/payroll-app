from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from app.shared.value_objects import AttendanceStatus


@dataclass(slots=True)
class Attendance:
    business_id: UUID
    employee_id: UUID
    date: date
    status: AttendanceStatus
    total_hours: Decimal | None = None
    marked_by: str | None = None
    notes: str | None = None
    overtime_hours: Decimal | None = None
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def create(
        cls,
        business_id: UUID,
        employee_id: UUID,
        date: date,
        status: AttendanceStatus,
        total_hours: Decimal | None = None,
        overtime_hours: Decimal | None = None,
        marked_by: str | None = None,
        notes: str | None = None,
    ) -> "Attendance":
        return cls(
            business_id=business_id,
            employee_id=employee_id,
            date=date,
            status=status,
            total_hours=total_hours,
            overtime_hours=overtime_hours,
            marked_by=marked_by,
            notes=notes,
        )

    def update_status(self, new_status: AttendanceStatus) -> None:
        self.status = new_status

    def set_overtime(self, hours: Decimal) -> None:
        self.overtime_hours = hours

    def replace_notes(self, new_notes: str | None) -> None:
        self.notes = new_notes
