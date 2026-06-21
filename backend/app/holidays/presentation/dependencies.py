from fastapi import Depends

from app.core.dependencies import get_uow
from app.core.uow import SqlAlchemyUnitOfWork
from app.holidays.application.use_cases import (
    CreateHolidayUseCase,
    ListHolidaysUseCase,
    RenameHolidayUseCase,
    DeleteHolidayUseCase,
    GetHolidayByDateUseCase,
)


def get_create_holiday_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> CreateHolidayUseCase:
    return CreateHolidayUseCase(uow)


def get_list_holidays_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ListHolidaysUseCase:
    return ListHolidaysUseCase(uow)


def get_rename_holiday_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> RenameHolidayUseCase:
    return RenameHolidayUseCase(uow)


def get_delete_holiday_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> DeleteHolidayUseCase:
    return DeleteHolidayUseCase(uow)


def get_get_holiday_by_date_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GetHolidayByDateUseCase:
    return GetHolidayByDateUseCase(uow)