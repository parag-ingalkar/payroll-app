from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.shared.value_objects import AttendanceStatus


@dataclass(slots=True)
class UpsertAttendanceCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID
    date: date
    status: AttendanceStatus | None = None
    total_hours: Decimal | None = None
    overtime_hours: Decimal | None = None
    marked_by: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class DeleteAttendanceCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID
    date: date


@dataclass(slots=True)
class ListAttendancesByDateCommand:
    business_id: UUID
    owner_id: str
    date: date
    status: AttendanceStatus | None = None


@dataclass(slots=True)
class ListAttendancesByMonthCommand:
    business_id: UUID
    owner_id: str
    year: int
    month: int
    status: AttendanceStatus | None = None


@dataclass(slots=True)
class GetEmployeeAttendanceDayCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID
    date: date


@dataclass(slots=True)
class GetEmployeeAttendanceMonthCommand:
    business_id: UUID
    owner_id: str
    employee_id: UUID
    year: int
    month: int


@dataclass(slots=True)
class BulkAttendanceEntry:
    employee_id: UUID
    status: AttendanceStatus
    overtime_hours: Decimal | None = None
    notes: str | None = None


@dataclass(slots=True)
class BulkUpsertAttendanceCommand:
    business_id: UUID
    owner_id: str
    date: date
    marked_by: str
    entries: list[BulkAttendanceEntry]