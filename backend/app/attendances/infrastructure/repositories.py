from collections.abc import Sequence
from datetime import date
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable
from uuid import UUID

from app.attendances.domain.value_objects import AttendanceSummary
from sqlalchemy import Numeric, case, cast, distinct, func, select, delete, extract
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
async def get_attendance_summary_for_employees(
    self,
    *,
    business_id: UUID,
    period_start_date: date,
    period_end_date: date,
    employee_ids: Sequence[UUID] | None = None,
) -> dict[UUID, "AttendanceSummary"]:
    A = AttendanceModel
    zero = Decimal("0.00")
    one = Decimal("1.00")

    stmt = (
        select(
            A.employee_id.label("employee_id"),
            func.array_agg(distinct(A.date)).label("attendance_days"),
            cast(
                func.coalesce(
                    func.sum(
                        case(
                            (A.status == AttendanceStatus.PRESENT, one),
                            else_=zero,
                        )
                    ),
                    zero,
                ),
                Numeric(10, 2),
            ).label("present_days"),
            cast(
                func.coalesce(
                    func.sum(
                        case(
                            (A.status == AttendanceStatus.HALF_DAY, one),
                            else_=zero,
                        )
                    ),
                    zero,
                ),
                Numeric(10, 2),
            ).label("half_days"),
            cast(
                func.coalesce(
                    func.sum(
                        case(
                            (A.status == AttendanceStatus.PAID_LEAVE, one),
                            else_=zero,
                        )
                    ),
                    zero,
                ),
                Numeric(10, 2),
            ).label("paid_leave_days"),
            cast(
                func.coalesce(
                    func.sum(
                        case(
                            (A.status == AttendanceStatus.UNPAID_LEAVE, one),
                            else_=zero,
                        )
                    ),
                    zero,
                ),
                Numeric(10, 2),
            ).label("unpaid_leave_days"),

            cast(
                func.coalesce(
                    func.sum(
                        case(
                            (A.status == AttendanceStatus.PAID_HOLIDAY, one),
                            else_=zero,
                        )
                    ),
                    zero,
                ),
                Numeric(10, 2),
            ).label("paid_holiday_days"),
            cast(
                func.coalesce(
                    func.sum(
                        case(
                            (A.status == AttendanceStatus.UNPAID_HOLIDAY, one),
                            else_=zero,
                        )
                    ),
                    zero,
                ),
                Numeric(10, 2),
            ).label("unpaid_holiday_days"),
            cast(
                func.coalesce(func.sum(A.overtime_hours), zero),
                Numeric(10, 2),
            ).label("overtime_hours"),
            cast(
                func.coalesce(func.sum(A.total_hours), zero),
                Numeric(10, 2),
            ).label("total_worked_hours"),
        )
        .where(
            A.business_id == business_id,
            A.date >= period_start_date,
            A.date <= period_end_date,
        )
        .group_by(A.employee_id)
    )

    if employee_ids:
        stmt = stmt.where(A.employee_id.in_(employee_ids))

    result = await self.session.execute(stmt)
    rows = result.all()

    summaries: dict[UUID, AttendanceSummary] = {}
    for row in rows:
        summaries[row.employee_id] = AttendanceSummary(
            employee_id=row.employee_id,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
            attendance_days=set(row.attendance_days or []),
            present_days=row.present_days,
            half_days=row.half_days,
            paid_leave_days=row.paid_leave_days,
            unpaid_leave_days=row.unpaid_leave_days,
            paid_holiday_days=row.paid_holiday_days,
            unpaid_holiday_days=row.unpaid_holiday_days,
            overtime_hours=row.overtime_hours,
            total_worked_hours=row.total_worked_hours,
        )

    return summaries