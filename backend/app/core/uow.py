from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.business.application.ports import (
    BusinessRepositoryPort,
)
from app.business.infrastructure.repositories import SqlAlchemyBusinessRepository


class UnitOfWorkPort(Protocol):
    businesses: BusinessRepositoryPort

    async def __aenter__(self) -> "UnitOfWorkPort": ...

    async def __aexit__(self, exc_type, exc, tb) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class SqlAlchemyUnitOfWork(UnitOfWorkPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession | None = None
        self.businesses: BusinessRepositoryPort

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.businesses = SqlAlchemyBusinessRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            if self.session is not None:
                await self.session.close()

    async def commit(self) -> None:
        if self.session is not None:
            await self.session.commit()

    async def rollback(self) -> None:
        if self.session is not None:
            await self.session.rollback()
