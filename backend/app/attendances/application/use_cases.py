from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Sequence
from uuid import UUID

from app.attendances.domain.exceptions import (
    AttendanceFutureDateError,
    AttendanceNotFoundError,
    AttendanceOnHolidayError,
    InactiveEmployeeAttendanceError,
)
from app.businesses.domain.entities import Business
from app.businesses.domain.exceptions import BusinessNotFoundError
from app.core.uow import UnitOfWorkPort
from app.attendances.application.commands import (
    UpsertAttendanceCommand,
    DeleteAttendanceCommand,
    ListAttendancesByDateCommand,
    ListAttendancesByMonthCommand,
    GetEmployeeAttendanceDayCommand,
    GetEmployeeAttendanceMonthCommand,
    BulkUpsertAttendanceCommand,
)
from app.attendances.domain.entities import Attendance
from app.employees.domain.exceptions import EmployeeNotFoundError


def _assert_not_future(d: date) -> None:
    if d > date.today():
        raise AttendanceFutureDateError(str(d))


async def _verify_business_and_owner(
    uow: UnitOfWorkPort, business_id: UUID, owner_id: str
) -> Business:
    business = await uow.businesses.get_by_id_and_owner(
        business_id=business_id, owner_id=owner_id
    )
    if not business:
        raise BusinessNotFoundError(
            f"Business with id {business_id} not found for owner {owner_id}."
        )
    return business


@dataclass(slots=True)
class UpsertAttendanceUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: UpsertAttendanceCommand) -> Attendance:
        async with self.uow as uow:
            _assert_not_future(cmd.date)

            business = await _verify_business_and_owner(
                uow, cmd.business_id, cmd.owner_id
            )

            if business.is_weekly_off(cmd.date):
                raise AttendanceOnHolidayError(
                    f"Cannot mark attendance on a weekly off day: {cmd.date}."
                )

            holiday = await uow.holidays.get_by_business_and_date(
                business_id=cmd.business_id,
                holiday_date=cmd.date,
            )
            if holiday:
                raise AttendanceOnHolidayError(
                    f"Cannot mark attendance on a holiday: {cmd.date}."
                )

            # Verify employee
            employee = await uow.employees.get_by_business_and_id(
                business_id=cmd.business_id,
                employee_id=cmd.employee_id,
            )
            if employee is None:
                raise EmployeeNotFoundError(
                    f"Employee with id {cmd.employee_id} not found for business {cmd.business_id}."
                )
            if not employee.is_active:
                raise InactiveEmployeeAttendanceError(str(cmd.employee_id))

            # Try to load existing attendance (for partial update)
            attendance = await uow.attendances.get_attendance(
                business_id=cmd.business_id,
                employee_id=cmd.employee_id,
                date=cmd.date,
            )

            if attendance is None:
                # New record: require status at minimum
                if cmd.status is None:
                    raise ValueError("status is required when creating attendance")
                attendance = Attendance.create(
                    business_id=cmd.business_id,
                    employee_id=cmd.employee_id,
                    date=cmd.date,
                    status=cmd.status,
                    total_hours=cmd.total_hours,
                    overtime_hours=cmd.overtime_hours or Decimal("0"),
                    marked_by=cmd.marked_by,
                    notes=cmd.notes,
                )
            else:
                # Existing: apply only provided fields
                if cmd.status is not None:
                    attendance.update_status(cmd.status)
                if cmd.total_hours is not None:
                    attendance.total_hours = cmd.total_hours
                if cmd.overtime_hours is not None:
                    attendance.set_overtime(cmd.overtime_hours)
                if cmd.notes is not None:
                    attendance.replace_notes(cmd.notes)
                if cmd.marked_by is not None:
                    attendance.marked_by = cmd.marked_by

            await uow.attendances.upsert_attendance(attendance)
            await uow.commit()
            return attendance


@dataclass(slots=True)
class DeleteAttendanceUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: DeleteAttendanceCommand) -> None:
        async with self.uow as uow:
            _business = await _verify_business_and_owner(
                uow, cmd.business_id, cmd.owner_id
            )

            attendance = await uow.attendances.get_attendance(
                business_id=cmd.business_id,
                employee_id=cmd.employee_id,
                date=cmd.date,
            )
            if not attendance:
                raise AttendanceNotFoundError(
                    f"Attendance record not found for employee {cmd.employee_id} on {cmd.date}."
                )

            await uow.attendances.delete_attendance(attendance)
            await uow.commit()


@dataclass(slots=True)
class ListAttendancesByDateUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: ListAttendancesByDateCommand) -> Sequence[Attendance]:
        async with self.uow as uow:
            await _verify_business_and_owner(uow, cmd.business_id, cmd.owner_id)
            return await uow.attendances.list_by_date(
                business_id=cmd.business_id,
                date=cmd.date,
                status=cmd.status,
            )


@dataclass(slots=True)
class ListAttendancesByMonthUseCase:
    uow: UnitOfWorkPort

    async def execute(
        self, cmd: ListAttendancesByMonthCommand
    ) -> Sequence[Attendance]:
        async with self.uow as uow:
            await _verify_business_and_owner(uow, cmd.business_id, cmd.owner_id)
            return await uow.attendances.list_by_month(
                business_id=cmd.business_id,
                year=cmd.year,
                month=cmd.month,
                status=cmd.status,
            )


@dataclass(slots=True)
class GetEmployeeAttendanceDayUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: GetEmployeeAttendanceDayCommand) -> Attendance | None:
        async with self.uow as uow:
            await _verify_business_and_owner(uow, cmd.business_id, cmd.owner_id)
            return await uow.attendances.get_attendance(
                business_id=cmd.business_id,
                employee_id=cmd.employee_id,
                date=cmd.date,
            )


@dataclass(slots=True)
class GetEmployeeAttendanceMonthUseCase:
    uow: UnitOfWorkPort

    async def execute(
        self, cmd: GetEmployeeAttendanceMonthCommand
    ) -> Sequence[Attendance]:
        async with self.uow as uow:
            await _verify_business_and_owner(uow, cmd.business_id, cmd.owner_id)
            return await uow.attendances.list_employee_month(
                business_id=cmd.business_id,
                employee_id=cmd.employee_id,
                year=cmd.year,
                month=cmd.month,
            )


@dataclass(slots=True)
class BulkUpsertAttendanceUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: BulkUpsertAttendanceCommand) -> None:
        async with self.uow as uow:
            _assert_not_future(cmd.date)

            business = await _verify_business_and_owner(
                uow, cmd.business_id, cmd.owner_id
            )

            if business.is_weekly_off(cmd.date):
                raise AttendanceOnHolidayError(
                    f"Cannot mark attendance on a weekly off day: {cmd.date}."
                )

            holiday = await uow.holidays.get_by_business_and_date(
                business_id=cmd.business_id,
                holiday_date=cmd.date,
            )
            if holiday:
                raise AttendanceOnHolidayError(
                    f"Cannot mark attendance on a holiday: {cmd.date}."
                )

            # Single call to load all active employees for the business
            active_employees = await uow.employees.list_by_business(
                cmd.business_id, is_active=True
            )
            active_ids = {emp.id for emp in active_employees}

            entries_to_upsert: list[Attendance] = []
            for entry in cmd.entries:
                if entry.employee_id not in active_ids:
                    raise InactiveEmployeeAttendanceError(str(entry.employee_id))

                attendance = Attendance.create(
                    business_id=cmd.business_id,
                    employee_id=entry.employee_id,
                    date=cmd.date,
                    status=entry.status,
                    overtime_hours=entry.overtime_hours,
                    marked_by=cmd.marked_by,
                    notes=entry.notes,
                )
                entries_to_upsert.append(attendance)

            await uow.attendances.bulk_upsert_for_date(
                business_id=cmd.business_id,
                date=cmd.date,
                entries=entries_to_upsert,
                marked_by=cmd.marked_by,
            )
            await uow.commit()