from collections.abc import Sequence
from datetime import date
from typing import Protocol
from uuid import UUID

from app.attendance.domain.entities import Attendance, AttendanceStatus


class AttendanceRepositoryPort(Protocol):
    async def add(self, attendance: Attendance) -> None: ...

    async def get_by_employee_and_date(
        self, business_id: UUID, employee_id: UUID, date_: date
    ) -> Attendance | None: ...

    async def list_by_date(
        self,
        business_id: UUID,
        date_: date,
        employee_id: UUID | None = None,
        status: AttendanceStatus | None = None,
    ) -> Sequence[Attendance]: ...

    async def list_by_employee(
        self,
        business_id: UUID,
        employee_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        status: AttendanceStatus | None = None,
    ) -> Sequence[Attendance]: ...

    async def update(self, attendance: Attendance) -> None: ...

    async def delete(self, attendance: Attendance) -> None: ...

    async def upsert_many(
        self, attendances: list[Attendance]
    ) -> Sequence[Attendance]: ...

    async def list_for_employee_and_period(
        self,
        business_id: UUID,
        employee_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Sequence[Attendance]: ...
