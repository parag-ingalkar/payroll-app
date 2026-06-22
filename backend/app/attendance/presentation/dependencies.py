from fastapi import Depends

from app.attendance.application.use_cases import (
    BulkMarkAttendanceUseCase,
    DeleteAttendanceUseCase,
    GetAttendanceUseCase,
    ListAttendanceByDateUseCase,
    ListAttendanceByEmployeeUseCase,
    MarkAllPresentUseCase,
    MarkAttendanceUseCase,
    UpdateAttendanceUseCase,
)
from app.core.dependencies import get_uow
from app.core.uow import SqlAlchemyUnitOfWork


def get_mark_attendance_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MarkAttendanceUseCase:
    return MarkAttendanceUseCase(uow)


def get_update_attendance_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> UpdateAttendanceUseCase:
    return UpdateAttendanceUseCase(uow)


def get_delete_attendance_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> DeleteAttendanceUseCase:
    return DeleteAttendanceUseCase(uow)


def get_get_attendance_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GetAttendanceUseCase:
    return GetAttendanceUseCase(uow)


def get_list_attendance_by_date_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ListAttendanceByDateUseCase:
    return ListAttendanceByDateUseCase(uow)


def get_list_attendance_by_employee_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ListAttendanceByEmployeeUseCase:
    return ListAttendanceByEmployeeUseCase(uow)


def get_bulk_mark_attendance_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> BulkMarkAttendanceUseCase:
    return BulkMarkAttendanceUseCase(uow)


def get_mark_all_present_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MarkAllPresentUseCase:
    return MarkAllPresentUseCase(uow)
