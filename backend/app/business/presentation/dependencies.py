# app/business/presentation/router.py
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
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
from app.core.db import get_session_factory
from app.business.infrastructure.uow import SqlAlchemyBusinessUnitOfWork


@dataclass(slots=True)
class CurrentPrincipal:
    clerk_user_id: str


def get_current_user() -> CurrentPrincipal:
    # TODO: replace with real auth integration
    return CurrentPrincipal(clerk_user_id="demo-owner")


def get_business_uow(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> SqlAlchemyBusinessUnitOfWork:
    return SqlAlchemyBusinessUnitOfWork(session_factory)


def get_create_business_use_case(
    uow: SqlAlchemyBusinessUnitOfWork = Depends(get_business_uow),
) -> CreateBusinessUseCase:
    return CreateBusinessUseCase(uow)


def get_list_businesses_use_case(
    uow: SqlAlchemyBusinessUnitOfWork = Depends(get_business_uow),
) -> ListBusinessesUseCase:
    return ListBusinessesUseCase(uow)


def get_get_business_use_case(
    uow: SqlAlchemyBusinessUnitOfWork = Depends(get_business_uow),
) -> GetBusinessUseCase:
    return GetBusinessUseCase(uow)


def get_update_business_use_case(
    uow: SqlAlchemyBusinessUnitOfWork = Depends(get_business_uow),
) -> UpdateBusinessUseCase:
    return UpdateBusinessUseCase(uow)


def get_delete_business_use_case(
    uow: SqlAlchemyBusinessUnitOfWork = Depends(get_business_uow),
) -> DeleteBusinessUseCase:
    return DeleteBusinessUseCase(uow)


def get_get_weekly_off_rules_use_case(
    uow: SqlAlchemyBusinessUnitOfWork = Depends(get_business_uow),
) -> GetWeeklyOffRulesUseCase:
    return GetWeeklyOffRulesUseCase(uow)


def get_replace_weekly_off_rules_use_case(
    uow: SqlAlchemyBusinessUnitOfWork = Depends(get_business_uow),
) -> ReplaceWeeklyOffRulesUseCase:
    return ReplaceWeeklyOffRulesUseCase(uow)
