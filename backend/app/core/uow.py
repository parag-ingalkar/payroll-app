from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.attendances.application.ports import AttendanceRepositoryPort
from app.attendances.infrastructure.repositories import SqlAttendanceRepository
from app.businesses.application.ports import BusinessRepositoryPort
from app.businesses.infrastructure.repositories import SqlBusinessRepository
from app.holidays.application.ports import HolidaysRepositoryPort
from app.holidays.infrastructure.repositories import SqlHolidaysRepository
from app.employees.application.ports import EmployeeRepositoryPort
from app.employees.infrastructure.repositories import SqlEmployeeRepository


class UnitOfWorkPort(Protocol):
    attendances: AttendanceRepositoryPort
    businesses: BusinessRepositoryPort
    holidays: HolidaysRepositoryPort
    employees: EmployeeRepositoryPort

    async def __aenter__(self) -> "UnitOfWorkPort": ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class SqlAlchemyUnitOfWork(UnitOfWorkPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession | None = None
        self.attendances: AttendanceRepositoryPort
        self.businesses: BusinessRepositoryPort
        self.holidays: HolidaysRepositoryPort
        self.employees: EmployeeRepositoryPort

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.businesses = SqlBusinessRepository(self.session)
        self.holidays = SqlHolidaysRepository(self.session)
        self.employees = SqlEmployeeRepository(self.session)
        self.attendances = SqlAttendanceRepository(self.session)
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
