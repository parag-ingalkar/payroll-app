from dataclasses import dataclass
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)
from fastapi import Depends
from app.core.db import async_session_factory, get_session_factory
from app.core.uow import SqlAlchemyUnitOfWork


async def get_db():
    async with async_session_factory() as session:
        yield session


def get_uow(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory)


@dataclass(slots=True)
class CurrentPrincipal:
    clerk_user_id: str


def get_current_user() -> CurrentPrincipal:
    # TODO: replace with real auth integration
    return CurrentPrincipal(clerk_user_id="demo-owner")
