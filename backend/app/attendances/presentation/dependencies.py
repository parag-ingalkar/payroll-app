from fastapi import Depends

from app.core.dependencies import get_uow
from app.core.uow import SqlAlchemyUnitOfWork
from app.attendances.application.use_cases import (
    UpsertAttendanceUseCase,
    DeleteAttendanceUseCase,
    ListAttendancesByDateUseCase,
    ListAttendancesByMonthUseCase,
    GetEmployeeAttendanceDayUseCase,
    GetEmployeeAttendanceMonthUseCase,
    BulkUpsertAttendanceUseCase,
)


def get_upsert_attendance_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> UpsertAttendanceUseCase:
    return UpsertAttendanceUseCase(uow)


def get_delete_attendance_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> DeleteAttendanceUseCase:
    return DeleteAttendanceUseCase(uow)


def get_list_attendances_by_date_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ListAttendancesByDateUseCase:
    return ListAttendancesByDateUseCase(uow)


def get_list_attendances_by_month_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ListAttendancesByMonthUseCase:
    return ListAttendancesByMonthUseCase(uow)


def get_get_employee_attendance_day_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GetEmployeeAttendanceDayUseCase:
    return GetEmployeeAttendanceDayUseCase(uow)


def get_get_employee_attendance_month_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GetEmployeeAttendanceMonthUseCase:
    return GetEmployeeAttendanceMonthUseCase(uow)


def get_bulk_upsert_attendance_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> BulkUpsertAttendanceUseCase:
    return BulkUpsertAttendanceUseCase(uow)