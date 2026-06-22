from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.attendance.application.ports import AttendanceRepositoryPort
from app.attendance.domain.entities import Attendance, AttendanceStatus
from app.attendance.infrastructure.orm import AttendanceModel


class SqlAlchemyAttendanceRepository(AttendanceRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, attendance: Attendance) -> None:
        model = AttendanceModel.from_entity(attendance)
        self.session.add(model)
        await self.session.flush()

    async def get_by_employee_and_date(
        self, business_id: UUID, employee_id: UUID, date_: date
    ) -> Attendance | None:
        result = await self.session.execute(
            select(AttendanceModel).where(
                AttendanceModel.business_id == business_id,
                AttendanceModel.employee_id == employee_id,
                AttendanceModel.date == date_,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list_by_date(
        self,
        business_id: UUID,
        date_: date,
        employee_id: UUID | None = None,
        status: AttendanceStatus | None = None,
    ) -> Sequence[Attendance]:
        stmt = select(AttendanceModel).where(
            AttendanceModel.business_id == business_id,
            AttendanceModel.date == date_,
        )
        if employee_id is not None:
            stmt = stmt.where(AttendanceModel.employee_id == employee_id)
        if status is not None:
            stmt = stmt.where(AttendanceModel.status == status)
        result = await self.session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def list_by_employee(
        self,
        business_id: UUID,
        employee_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        status: AttendanceStatus | None = None,
    ) -> Sequence[Attendance]:
        stmt = select(AttendanceModel).where(
            AttendanceModel.business_id == business_id,
            AttendanceModel.employee_id == employee_id,
        )
        if start_date is not None:
            stmt = stmt.where(AttendanceModel.date >= start_date)
        if end_date is not None:
            stmt = stmt.where(AttendanceModel.date <= end_date)
        if status is not None:
            stmt = stmt.where(AttendanceModel.status == status)
        stmt = stmt.order_by(AttendanceModel.date)
        result = await self.session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def update(self, attendance: Attendance) -> None:
        result = await self.session.execute(
            select(AttendanceModel).where(
                AttendanceModel.business_id == attendance.business_id,
                AttendanceModel.employee_id == attendance.employee_id,
                AttendanceModel.date == attendance.date,
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return
        model.status = attendance.status
        model.overtime_hours = attendance.overtime_hours
        await self.session.flush()

    async def delete(self, attendance: Attendance) -> None:
        result = await self.session.execute(
            select(AttendanceModel).where(
                AttendanceModel.business_id == attendance.business_id,
                AttendanceModel.employee_id == attendance.employee_id,
                AttendanceModel.date == attendance.date,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)

    async def upsert_many(self, attendances: list[Attendance]) -> Sequence[Attendance]:
        if not attendances:
            return []

        values = [
            {
                "id": a.id,
                "business_id": a.business_id,
                "employee_id": a.employee_id,
                "date": a.date,
                "status": a.status.value,
                "overtime_hours": a.overtime_hours,
            }
            for a in attendances
        ]

        stmt = pg_insert(AttendanceModel).values(values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_attendance_business_employee_date",
            set_={
                "status": stmt.excluded.status,
                "overtime_hours": stmt.excluded.overtime_hours,
            },
        ).returning(
            AttendanceModel.id,
            AttendanceModel.business_id,
            AttendanceModel.employee_id,
            AttendanceModel.date,
            AttendanceModel.status,
            AttendanceModel.overtime_hours,
        )

        result = await self.session.execute(stmt)
        rows = result.fetchall()
        return [
            Attendance(
                id=row.id,
                business_id=row.business_id,
                employee_id=row.employee_id,
                date=row.date,
                status=AttendanceStatus(row.status),
                overtime_hours=row.overtime_hours,
            )
            for row in rows
        ]
