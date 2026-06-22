from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.attendance.domain.entities import AttendanceStatus


class AttendanceCreate(BaseModel):
    employee_id: UUID
    date: date
    status: AttendanceStatus
    overtime_hours: Decimal = Field(default=Decimal("0"), ge=0, le=12)


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus | None = None
    overtime_hours: Decimal | None = Field(default=None, ge=0, le=12)


class AttendanceRead(BaseModel):
    id: UUID
    business_id: UUID
    employee_id: UUID
    date: date
    status: AttendanceStatus
    overtime_hours: Decimal

    model_config = ConfigDict(from_attributes=True)


class BulkAttendanceItem(BaseModel):
    employee_id: UUID
    status: AttendanceStatus
    overtime_hours: Decimal = Field(default=Decimal("0"), ge=0, le=12)


class BulkMarkAttendanceRequest(BaseModel):
    date: date
    entries: list[BulkAttendanceItem] = Field(..., min_length=1)


class MarkAllPresentRequest(BaseModel):
    date: date
