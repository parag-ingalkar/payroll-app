# app/business/presentation/router.py
from fastapi import Depends

from app.business.application.use_cases import (
    CreateBusinessUseCase,
    ListBusinessesUseCase,
    GetBusinessUseCase,
    UpdateBusinessUseCase,
    DeleteBusinessUseCase,
    GetWeeklyOffRulesUseCase,
    ReplaceWeeklyOffRulesUseCase,
)
from app.core.uow import SqlAlchemyUnitOfWork
from app.core.dependencies import get_uow


def get_create_business_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> CreateBusinessUseCase:
    return CreateBusinessUseCase(uow)


def get_list_businesses_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ListBusinessesUseCase:
    return ListBusinessesUseCase(uow)


def get_get_business_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GetBusinessUseCase:
    return GetBusinessUseCase(uow)


def get_update_business_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> UpdateBusinessUseCase:
    return UpdateBusinessUseCase(uow)


def get_delete_business_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> DeleteBusinessUseCase:
    return DeleteBusinessUseCase(uow)


def get_get_weekly_off_rules_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GetWeeklyOffRulesUseCase:
    return GetWeeklyOffRulesUseCase(uow)


def get_replace_weekly_off_rules_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ReplaceWeeklyOffRulesUseCase:
    return ReplaceWeeklyOffRulesUseCase(uow)
