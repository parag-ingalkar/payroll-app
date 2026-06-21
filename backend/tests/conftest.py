# tests/integration/conftest.py
from datetime import date
import os
from uuid import UUID
from collections.abc import AsyncGenerator
from decimal import Decimal

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://testuser:testpassword@localhost:5433/payrolldb_test"
)

import pytest

from httpx2 import ASGITransport, AsyncClient  # type: ignore
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.db import Base, get_session_factory
from app.business.infrastructure.orm import BusinessModel, BusinessWeeklyOffRuleModel  # noqa: F401
from app.core.uow import SqlAlchemyUnitOfWork
from app.main import app
from app.business.domain.entities import WageType, WeeklyOffRule, Weekday


pytest_plugins = ["anyio"]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def session_factory(
    test_engine: AsyncEngine,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    # Open a dedicated connection for this test
    async with test_engine.connect() as conn:
        # Begin an outer transaction for the test
        trans = await conn.begin()

        # Bind the session factory to this connection
        factory = async_sessionmaker(
            bind=conn,
            expire_on_commit=False,
        )

        try:
            yield factory
        finally:
            # Roll back everything done in this test
            if trans.is_active:
                await trans.rollback()


@pytest.fixture
async def sqlalchemy_uow(
    session_factory: async_sessionmaker[AsyncSession],
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory)


@pytest.fixture
async def api_client(
    test_engine: AsyncEngine,
) -> AsyncGenerator[AsyncClient, None]:
    """
    - Open a dedicated DB connection & transaction for this test.
    - Build a session factory bound to that connection.
    - Override get_session_factory to return this factory.
    - Run the app via AsyncClient and ASGITransport.
    - Roll back and cleanup after the test.
    """
    # open connection and transaction
    conn = await test_engine.connect()
    trans = await conn.begin()

    session_factory = async_sessionmaker(bind=conn, expire_on_commit=False)

    async def override_get_session_factory():
        return session_factory

    app.dependency_overrides[get_session_factory] = override_get_session_factory

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        try:
            yield client
        finally:
            app.dependency_overrides.pop(get_session_factory, None)
            if trans.is_active:
                await trans.rollback()
            await conn.close()


@pytest.fixture
def business_defaults() -> dict:
    return {
        "owner_id": "owner-1",
        "name": "Test Business",
        "default_wage_type": WageType.HOURLY,
        "default_working_hours_per_day": Decimal("8.0"),
        "default_overtime_multiplier": Decimal("1.5"),
        "payroll_start_day": 1,
        "weekly_off_rules": [
            WeeklyOffRule(weekday=Weekday.MONDAY, week_of_month=None),
            WeeklyOffRule(weekday=Weekday.TUESDAY, week_of_month=2),
        ],
    }


@pytest.fixture
def holiday_defaults():
    return {
        "business_id": UUID("12345678-1234-5678-1234-567812345678"),
        "date_": date(2026, 1, 1),
        "name": "New Year's Day",
    }
