# tests/conftest.py
import os
from collections.abc import AsyncGenerator
from decimal import Decimal

# Ensure tests use the test database
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

from app.business.domain.entities import WageType, Weekday, WeeklyOffRule
from app.core.db import Base, get_session_factory
from app.core.uow import SqlAlchemyUnitOfWork
from app.main import app


pytest_plugins = ["anyio"]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest.fixture
async def session_factory(
    test_engine: AsyncEngine,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    # Open a dedicated connection for this test
    async with test_engine.connect() as conn:
        # begin an outer transaction
        trans = await conn.begin()

        factory = async_sessionmaker(bind=conn, expire_on_commit=False)

        try:
            yield factory
        finally:
            if trans.is_active:
                await trans.rollback()


@pytest.fixture
async def sqlalchemy_uow(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[SqlAlchemyUnitOfWork, None]:
    uow = SqlAlchemyUnitOfWork(session_factory)
    async with uow:
        # __aenter__ runs here
        yield uow
        # __aexit__ runs when fixture ends


@pytest.fixture
async def api_client(
    test_engine: AsyncEngine,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Per-test DB transaction bound to FastAPI app via get_session_factory override.
    """
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
        "owner_id": "demo-owner",
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
