from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.shared.value_objects import AttendanceStatus


class AttendanceBase(BaseModel):
    date: date
    status: AttendanceStatus
    total_hours: Decimal | None = None
    overtime_hours: Decimal | None = None
    notes: str | None = None

class AttendanceUpsert(AttendanceBase):
    employee_id: UUID

# class AttendanceCreate(AttendanceBase):
#     """
#     Used for first-time or subsequent upsert of a single employee's attendance for a day.
#     Requires status; other fields optional.
#     """
#     employee_id: UUID


# class AttendanceUpdate(BaseModel):
#     """
#     Partial update/upsert; all fields optional.
#     """
#     status: AttendanceStatus | None = None
#     total_hours: Decimal | None = None
#     overtime_hours: Decimal | None = None
#     marked_by: str | None = None
#     notes: str | None = None


class AttendanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    employee_id: UUID
    date: date
    status: AttendanceStatus
    total_hours: Decimal | None = None
    overtime_hours: Decimal
    marked_by: str | None = None
    notes: str | None = None


class BulkAttendanceEntry(BaseModel):
    employee_id: UUID
    status: AttendanceStatus
    overtime_hours: Decimal | None = None
    notes: str | None = None


class BulkAttendanceCreate(BaseModel):
    """
    Used for grid-style bulk upsert of a specific date.
    """
    date: date
    entries: list[BulkAttendanceEntry]
