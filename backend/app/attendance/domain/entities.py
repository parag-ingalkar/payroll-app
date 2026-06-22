from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID

from app.attendance.domain.exceptions import OvertimeNotAllowedError


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    PAID_LEAVE = "paid_leave"
    UNPAID_LEAVE = "unpaid_leave"
    HALF_DAY = "half_day"


@dataclass
class Attendance:
    id: UUID
    business_id: UUID
    employee_id: UUID
    date: date
    status: AttendanceStatus
    overtime_hours: Decimal = field(default_factory=lambda: Decimal("0"))

    @classmethod
    def create(
        cls,
        id: UUID,
        business_id: UUID,
        employee_id: UUID,
        date: date,
        status: AttendanceStatus,
        overtime_hours: Decimal = Decimal("0"),
    ) -> "Attendance":
        instance = cls(
            id=id,
            business_id=business_id,
            employee_id=employee_id,
            date=date,
            status=status,
            overtime_hours=Decimal("0"),
        )
        if overtime_hours > Decimal("0"):
            instance.set_overtime(overtime_hours)
        return instance

    def update_status(self, new_status: AttendanceStatus) -> None:
        """Update attendance status. Clears overtime if changed away from PRESENT."""
        if new_status != AttendanceStatus.PRESENT:
            self.overtime_hours = Decimal("0")
        self.status = new_status

    def set_overtime(self, hours: Decimal) -> None:
        """Set overtime hours. Only allowed when status is PRESENT."""
        if self.status != AttendanceStatus.PRESENT:
            raise OvertimeNotAllowedError(
                f"Overtime hours can only be set when attendance is Present, "
                f"not '{self.status.value}'."
            )
        self.overtime_hours = hours
