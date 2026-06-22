from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.attendance.application.commands import (
    BulkMarkAttendanceCommand,
    DeleteAttendanceCommand,
    GetAttendanceCommand,
    ListAttendanceByDateCommand,
    ListAttendanceByEmployeeCommand,
    MarkAllPresentCommand,
    MarkAttendanceCommand,
    UpdateAttendanceCommand,
)
from app.attendance.domain.entities import Attendance, AttendanceStatus
from app.attendance.domain.exceptions import (
    AttendanceAlreadyExistsError,
    AttendanceFutureDateError,
    AttendanceNotFoundError,
    AttendanceOnHolidayError,
    AttendanceOnWeeklyOffError,
    InactiveEmployeeAttendanceError,
)
from app.business.domain.exceptions import BusinessNotFoundError
from app.core.uow import UnitOfWorkPort
from app.employees.domain.exceptions import EmployeeNotFoundError


def _assert_not_future(d: date) -> None:
    if d > date.today():
        raise AttendanceFutureDateError(str(d))


@dataclass
class MarkAttendanceUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: MarkAttendanceCommand) -> Attendance:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            _assert_not_future(cmd.date)

            holiday = await uow.holidays.get_by_business_and_date(
                business_id=cmd.business_id, date_=cmd.date
            )
            if holiday is not None:
                raise AttendanceOnHolidayError(str(cmd.date))

            if business.is_weekly_off(cmd.date):
                raise AttendanceOnWeeklyOffError(str(cmd.date))

            employee = await uow.employees.get_by_business_and_id(
                business_id=cmd.business_id, employee_id=cmd.employee_id
            )
            if employee is None:
                raise EmployeeNotFoundError(
                    business_id=str(cmd.business_id),
                    employee_id=str(cmd.employee_id),
                )
            if not employee.is_active:
                raise InactiveEmployeeAttendanceError(str(cmd.employee_id))

            existing = await uow.attendance.get_by_employee_and_date(
                business_id=cmd.business_id,
                employee_id=cmd.employee_id,
                date_=cmd.date,
            )
            if existing is not None:
                raise AttendanceAlreadyExistsError(
                    employee_id=str(cmd.employee_id), date=str(cmd.date)
                )

            attendance = Attendance.create(
                id=uuid4(),
                business_id=cmd.business_id,
                employee_id=cmd.employee_id,
                date=cmd.date,
                status=cmd.status,
                overtime_hours=cmd.overtime_hours,
            )
            await uow.attendance.add(attendance)
            await uow.commit()
            return attendance


@dataclass
class UpdateAttendanceUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: UpdateAttendanceCommand) -> Attendance:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            attendance = await uow.attendance.get_by_employee_and_date(
                business_id=cmd.business_id,
                employee_id=cmd.employee_id,
                date_=cmd.date,
            )
            if attendance is None:
                raise AttendanceNotFoundError(
                    employee_id=str(cmd.employee_id), date=str(cmd.date)
                )

            # Apply status first — entity clears overtime when moving away from PRESENT
            if "status" in cmd.fields_to_update and cmd.status is not None:
                attendance.update_status(cmd.status)

            # Apply overtime — entity raises OvertimeNotAllowedError if status is not PRESENT
            if (
                "overtime_hours" in cmd.fields_to_update
                and cmd.overtime_hours is not None
            ):
                attendance.set_overtime(cmd.overtime_hours)

            await uow.attendance.update(attendance)
            await uow.commit()
            return attendance


@dataclass
class DeleteAttendanceUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: DeleteAttendanceCommand) -> None:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            attendance = await uow.attendance.get_by_employee_and_date(
                business_id=cmd.business_id,
                employee_id=cmd.employee_id,
                date_=cmd.date,
            )
            if attendance is None:
                raise AttendanceNotFoundError(
                    employee_id=str(cmd.employee_id), date=str(cmd.date)
                )

            await uow.attendance.delete(attendance)
            await uow.commit()


@dataclass
class GetAttendanceUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: GetAttendanceCommand) -> Attendance:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            attendance = await uow.attendance.get_by_employee_and_date(
                business_id=cmd.business_id,
                employee_id=cmd.employee_id,
                date_=cmd.date,
            )
            if attendance is None:
                raise AttendanceNotFoundError(
                    employee_id=str(cmd.employee_id), date=str(cmd.date)
                )

            return attendance


@dataclass
class ListAttendanceByDateUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: ListAttendanceByDateCommand) -> Sequence[Attendance]:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            return await uow.attendance.list_by_date(
                business_id=cmd.business_id,
                date_=cmd.date,
                employee_id=cmd.employee_id,
                status=cmd.status,
            )


@dataclass
class ListAttendanceByEmployeeUseCase:
    uow: UnitOfWorkPort

    async def execute(
        self, cmd: ListAttendanceByEmployeeCommand
    ) -> Sequence[Attendance]:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            employee = await uow.employees.get_by_business_and_id(
                business_id=cmd.business_id, employee_id=cmd.employee_id
            )
            if employee is None:
                raise EmployeeNotFoundError(
                    business_id=str(cmd.business_id),
                    employee_id=str(cmd.employee_id),
                )

            return await uow.attendance.list_by_employee(
                business_id=cmd.business_id,
                employee_id=cmd.employee_id,
                start_date=cmd.start_date,
                end_date=cmd.end_date,
                status=cmd.status,
            )


@dataclass
class BulkMarkAttendanceUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: BulkMarkAttendanceCommand) -> Sequence[Attendance]:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            _assert_not_future(cmd.date)

            holiday = await uow.holidays.get_by_business_and_date(
                business_id=cmd.business_id, date_=cmd.date
            )
            if holiday is not None:
                raise AttendanceOnHolidayError(str(cmd.date))

            if business.is_weekly_off(cmd.date):
                raise AttendanceOnWeeklyOffError(str(cmd.date))

            attendances: list[Attendance] = []
            for entry in cmd.entries:
                employee = await uow.employees.get_by_business_and_id(
                    business_id=cmd.business_id, employee_id=entry.employee_id
                )
                if employee is None:
                    raise EmployeeNotFoundError(
                        business_id=str(cmd.business_id),
                        employee_id=str(entry.employee_id),
                    )
                if not employee.is_active:
                    raise InactiveEmployeeAttendanceError(str(entry.employee_id))

                attendances.append(
                    Attendance.create(
                        id=uuid4(),
                        business_id=cmd.business_id,
                        employee_id=entry.employee_id,
                        date=cmd.date,
                        status=entry.status,
                        overtime_hours=entry.overtime_hours,
                    )
                )

            result = await uow.attendance.upsert_many(attendances)
            await uow.commit()
            return result


@dataclass
class MarkAllPresentUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: MarkAllPresentCommand) -> Sequence[Attendance]:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with id {cmd.business_id} not found for owner {cmd.owner_id}."
                )

            _assert_not_future(cmd.date)

            holiday = await uow.holidays.get_by_business_and_date(
                business_id=cmd.business_id, date_=cmd.date
            )
            if holiday is not None:
                raise AttendanceOnHolidayError(str(cmd.date))

            if business.is_weekly_off(cmd.date):
                raise AttendanceOnWeeklyOffError(str(cmd.date))

            active_employees = await uow.employees.list_by_business(
                business_id=cmd.business_id, is_active=True
            )

            if not active_employees:
                return []

            attendances = [
                Attendance.create(
                    id=uuid4(),
                    business_id=cmd.business_id,
                    employee_id=emp.id,
                    date=cmd.date,
                    status=AttendanceStatus.PRESENT,
                    overtime_hours=Decimal("0"),
                )
                for emp in active_employees
            ]

            result = await uow.attendance.upsert_many(attendances)
            await uow.commit()
            return result
