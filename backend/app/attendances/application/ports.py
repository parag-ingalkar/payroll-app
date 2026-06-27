from datetime import date
from typing import Protocol, Iterable, Sequence
from uuid import UUID

from app.shared.value_objects import AttendanceStatus
from app.attendances.domain.entities import Attendance


class AttendanceRepositoryPort(Protocol):
    # Single-day create or update (idempotent per business+employee+date)
    async def upsert_attendance(
        self,
        attendance: Attendance,
    ) -> None: ...

    # Delete a specific day entry
    async def delete_attendance(
        self,
        attendance: Attendance,
    ) -> None: ...

    # Get a single attendance record (or None)
    async def get_attendance(
        self,
        *,
        business_id: UUID,
        employee_id: UUID,
        date: date,
    ) -> Attendance | None: ...

    # List all attendances for a business on a given date
    async def list_by_date(
        self,
        *,
        business_id: UUID,
        date: date,
        status: AttendanceStatus | None = None,
    ) -> Sequence[Attendance]: ...

    # List all attendances for a business in a given month
    async def list_by_month(
        self,
        *,
        business_id: UUID,
        year: int,
        month: int,
        status: AttendanceStatus | None = None,
    ) -> Sequence[Attendance]: ...

    # List all attendances for a single employee in a month
    async def list_employee_month(
        self,
        *,
        business_id: UUID,
        employee_id: UUID,
        year: int,
        month: int,
    ) -> Sequence[Attendance]: ...

    # Bulk upsert for one date (grid marking)
    async def bulk_upsert_for_date(
        self,
        *,
        business_id: UUID,
        date: date,
        entries: Iterable[Attendance],
        marked_by: str | None,
    ) -> None: ...