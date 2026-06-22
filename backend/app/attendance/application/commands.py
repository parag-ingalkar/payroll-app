from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.attendance.domain.entities import AttendanceStatus


@dataclass(slots=True)
class MarkAttendanceCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID
    date: date
    status: AttendanceStatus
    overtime_hours: Decimal = Decimal("0")


@dataclass(slots=True)
class UpdateAttendanceCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID
    date: date
    fields_to_update: frozenset[str]
    status: AttendanceStatus | None = None
    overtime_hours: Decimal | None = None


@dataclass(slots=True)
class DeleteAttendanceCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID
    date: date


@dataclass(slots=True)
class GetAttendanceCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID
    date: date


@dataclass(slots=True)
class ListAttendanceByDateCommand:
    business_id: UUID
    owner_id: str
    date: date
    employee_id: UUID | None = None
    status: AttendanceStatus | None = None


@dataclass(slots=True)
class ListAttendanceByEmployeeCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID
    start_date: date | None = None
    end_date: date | None = None
    status: AttendanceStatus | None = None


@dataclass
class BulkAttendanceEntry:
    employee_id: UUID
    status: AttendanceStatus
    overtime_hours: Decimal = field(default_factory=lambda: Decimal("0"))


@dataclass(slots=True)
class BulkMarkAttendanceCommand:
    business_id: UUID
    owner_id: str
    date: date
    entries: list[BulkAttendanceEntry]


@dataclass(slots=True)
class MarkAllPresentCommand:
    business_id: UUID
    owner_id: str
    date: date
