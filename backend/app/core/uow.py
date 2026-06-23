from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.attendance.application.ports import AttendanceRepositoryPort
from app.attendance.infrastructure.repository import SqlAlchemyAttendanceRepository
from app.business.application.ports import BusinessRepositoryPort
from app.business.infrastructure.repositories import SqlAlchemyBusinessRepository
from app.employees.application.ports import EmployeeRepositoryPort
from app.employees.infrastructure.repositories import SqlAlchemyEmployeeRepository
from app.holidays.application.ports import HolidayRepositoryPort
from app.holidays.infrastructure.repositories import SqlAlchemyHolidayRepository
from app.payroll.application.ports import PayrollRepositoryPort
from app.payroll.infrastructure.repository import SqlAlchemyPayrollRepository


class UnitOfWorkPort(Protocol):
    businesses: BusinessRepositoryPort
    holidays: HolidayRepositoryPort
    employees: EmployeeRepositoryPort
    attendance: AttendanceRepositoryPort
    payroll: PayrollRepositoryPort

    async def __aenter__(self) -> "UnitOfWorkPort": ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class SqlAlchemyUnitOfWork(UnitOfWorkPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession | None = None
        self.businesses: BusinessRepositoryPort
        self.holidays: HolidayRepositoryPort
        self.employees: EmployeeRepositoryPort
        self.attendance: AttendanceRepositoryPort
        self.payroll: PayrollRepositoryPort

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.businesses = SqlAlchemyBusinessRepository(self.session)
        self.holidays = SqlAlchemyHolidayRepository(self.session)
        self.employees = SqlAlchemyEmployeeRepository(self.session)
        self.attendance = SqlAlchemyAttendanceRepository(self.session)
        self.payroll = SqlAlchemyPayrollRepository(self.session)
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
