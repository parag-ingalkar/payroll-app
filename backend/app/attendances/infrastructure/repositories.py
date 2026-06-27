from collections.abc import Sequence
from datetime import date
from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from sqlalchemy import select, delete, extract
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.attendances.application.ports import AttendanceRepositoryPort
from app.attendances.domain.entities import Attendance
from app.attendances.infrastructure.models import AttendanceModel
from app.shared.value_objects import AttendanceStatus


@dataclass(slots=True)
class SqlAttendanceRepository(AttendanceRepositoryPort):
    session: AsyncSession

    async def upsert_attendance(self, attendance: Attendance) -> None:
        stmt = (
            pg_insert(AttendanceModel)
            .values(
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
            .on_conflict_do_update(
                index_elements=["business_id", "employee_id", "date"],
                set_={
                    "status": pg_insert(AttendanceModel).excluded.status,
                    "total_hours": pg_insert(AttendanceModel).excluded.total_hours,
                    "overtime_hours": pg_insert(
                        AttendanceModel
                    ).excluded.overtime_hours,
                    "marked_by": pg_insert(AttendanceModel).excluded.marked_by,
                    "notes": pg_insert(AttendanceModel).excluded.notes,
                },
            )
        )
        await self.session.execute(stmt)

    async def delete_attendance(self, attendance: Attendance) -> None:
        stmt = delete(AttendanceModel).where(AttendanceModel.id == attendance.id)
        await self.session.execute(stmt)

    async def get_attendance(
        self,
        *,
        business_id: UUID,
        employee_id: UUID,
        date: date,
    ) -> Attendance | None:
        stmt = select(AttendanceModel).where(
            AttendanceModel.business_id == business_id,
            AttendanceModel.employee_id == employee_id,
            AttendanceModel.date == date,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list_by_date(
        self,
        *,
        business_id: UUID,
        date: date,
        status: AttendanceStatus | None = None,
    ) -> Sequence[Attendance]:
        stmt = select(AttendanceModel).where(
            AttendanceModel.business_id == business_id,
            AttendanceModel.date == date,
        )
        if status is not None:
            stmt = stmt.where(AttendanceModel.status == status)
        result = await self.session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def list_by_month(
        self,
        *,
        business_id: UUID,
        year: int,
        month: int,
        status: AttendanceStatus | None = None,
    ) -> Sequence[Attendance]:
        stmt = select(AttendanceModel).where(
            AttendanceModel.business_id == business_id,
            extract("year", AttendanceModel.date) == year,
            extract("month", AttendanceModel.date) == month,
        )
        if status is not None:
            stmt = stmt.where(AttendanceModel.status == status)
        result = await self.session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def list_employee_month(
        self,
        *,
        business_id: UUID,
        employee_id: UUID,
        year: int,
        month: int,
    ) -> Sequence[Attendance]:
        stmt = select(AttendanceModel).where(
            AttendanceModel.business_id == business_id,
            AttendanceModel.employee_id == employee_id,
            extract("year", AttendanceModel.date) == year,
            extract("month", AttendanceModel.date) == month,
        )
        result = await self.session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def bulk_upsert_for_date(
        self,
        *,
        business_id: UUID,
        date: date,
        entries: Iterable[Attendance],
        marked_by: str | None,
    ) -> None:
        rows = [
            {
                "id": attendance.id,
                "business_id": business_id,
                "employee_id": attendance.employee_id,
                "date": date,
                "status": attendance.status,
                "total_hours": attendance.total_hours,
                "overtime_hours": attendance.overtime_hours,
                "marked_by": marked_by or attendance.marked_by,
                "notes": attendance.notes,
            }
            for attendance in entries
        ]
        if not rows:
            return

        stmt = (
            pg_insert(AttendanceModel)
            .values(rows)
            .on_conflict_do_update(
                index_elements=["business_id", "employee_id", "date"],
                set_={
                    "status": pg_insert(AttendanceModel).excluded.status,
                    "total_hours": pg_insert(AttendanceModel).excluded.total_hours,
                    "overtime_hours": pg_insert(
                        AttendanceModel
                    ).excluded.overtime_hours,
                    "marked_by": pg_insert(AttendanceModel).excluded.marked_by,
                    "notes": pg_insert(AttendanceModel).excluded.notes,
                },
            )
        )
        await self.session.execute(stmt)
