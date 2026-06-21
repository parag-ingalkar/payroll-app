# tests/integration/conftest.py
import pytest
from datetime import date
from uuid import UUID

from app.business.domain.entities import Business
from app.core.uow import SqlAlchemyUnitOfWork
from app.holidays.domain.entities import Holiday


@pytest.fixture
async def add_business_in_db(
    sqlalchemy_uow: SqlAlchemyUnitOfWork,
    business_defaults: dict,
) -> Business:
    business = Business.create(**business_defaults)
    business.id = UUID("12345678-1234-5678-1234-567812345678")
    await sqlalchemy_uow.businesses.add(business)
    await sqlalchemy_uow.commit()
    return business


@pytest.fixture
async def add_business_and_holiday_in_db(
    sqlalchemy_uow: SqlAlchemyUnitOfWork,
    add_business_in_db: Business,
) -> None:
    async with sqlalchemy_uow as uow:
        holiday = Holiday.create(
            business_id=add_business_in_db.id,
            date_=date(2026, 1, 1),
            name="New Year's Day",
        )
        await uow.holidays.add(holiday)
        await uow.commit()
