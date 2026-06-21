from datetime import date
from uuid import UUID

import pytest

from app.holidays.domain.entities import Holiday
from app.holidays.application.commands import (
    CreateHolidayCommand,
    DeleteHolidayCommand,
    GetHolidayByDateCommand,
    ListHolidaysCommand,
    RenameHolidayCommand,
)
from app.holidays.application.use_cases import (
    CreateHolidayUseCase,
    DeleteHolidayUseCase,
    GetHolidayByDateUseCase,
    ListHolidaysUseCase,
    RenameHolidayUseCase,
)


@pytest.mark.asyncio
async def test__create_holiday_with_valid_name(sqlalchemy_uow, add_business_in_db):
    create_uc = CreateHolidayUseCase(sqlalchemy_uow)

    cmd = CreateHolidayCommand(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        date=date(2026, 1, 1),
        name="New Year's Day",
    )

    created = await create_uc.execute(cmd)

    assert created.name == "New Year's Day"
    assert created.date == date(2026, 1, 1)

    # Assert DB state using a fresh UoW
    async with sqlalchemy_uow as uow:
        reloaded = await uow.holidays.get_by_business_and_date(
            business_id=created.business_id,
            date_=created.date,
        )
        assert reloaded is not None
        assert reloaded.id == created.id
        assert reloaded.name == "New Year's Day"


@pytest.mark.asyncio
async def test__create_holiday_with_empty_name(sqlalchemy_uow, add_business_in_db):
    create_uc = CreateHolidayUseCase(sqlalchemy_uow)

    cmd = CreateHolidayCommand(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        date=date(2026, 1, 1),
        name="   ",
    )

    holiday = await create_uc.execute(cmd)

    assert holiday.name is None
    assert holiday.date == date(2026, 1, 1)

    # Assert DB state using a fresh UoW
    async with sqlalchemy_uow as uow:
        reloaded = await uow.holidays.get_by_business_and_date(
            business_id=holiday.business_id,
            date_=holiday.date,
        )
        assert reloaded is not None
        assert reloaded.id == holiday.id
        assert reloaded.name is None


@pytest.mark.asyncio
async def test__rename_holiday_with_valid_name(
    sqlalchemy_uow, add_business_and_holiday_in_db
):
    rename_uc = RenameHolidayUseCase(sqlalchemy_uow)

    cmd = RenameHolidayCommand(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        date=date(2026, 1, 1),
        new_name="New Year's Celebration",
    )

    holiday = await rename_uc.execute(cmd)

    assert holiday.name == "New Year's Celebration"
    assert holiday.date == date(2026, 1, 1)

    # Assert DB state using a fresh UoW
    async with sqlalchemy_uow as uow:
        reloaded = await uow.holidays.get_by_business_and_date(
            business_id=holiday.business_id,
            date_=holiday.date,
        )
        assert reloaded is not None
        assert reloaded.id == holiday.id
        assert reloaded.name == "New Year's Celebration"


@pytest.mark.asyncio
async def test__list_holidays_by_month_use_case(sqlalchemy_uow, add_business_in_db):
    # Add holidays for the same business in different months
    async with sqlalchemy_uow as uow:
        holiday1 = Holiday.create(
            business_id=UUID("12345678-1234-5678-1234-567812345678"),
            date_=date(2026, 1, 1),
            name="New Year's Day",
        )
        holiday2 = Holiday.create(
            business_id=UUID("12345678-1234-5678-1234-567812345678"),
            date_=date(2026, 2, 14),
            name="Valentine's Day",
        )
        await uow.holidays.add(holiday1)
        await uow.holidays.add(holiday2)
        await uow.commit()

    list_uc = ListHolidaysUseCase(sqlalchemy_uow)

    cmd = ListHolidaysCommand(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        year=2026,
        month=2,
    )

    holidays = await list_uc.execute(cmd)

    assert len(holidays) == 1
    assert holidays[0].name == "Valentine's Day"
    assert holidays[0].date == date(2026, 2, 14)


@pytest.mark.asyncio
async def test__list_holidays_by_year_use_case(sqlalchemy_uow, add_business_in_db):
    # Add holidays for the same business in different years
    async with sqlalchemy_uow as uow:
        holiday1 = Holiday.create(
            business_id=UUID("12345678-1234-5678-1234-567812345678"),
            date_=date(2026, 1, 1),
            name="New Year's Day",
        )
        holiday2 = Holiday.create(
            business_id=UUID("12345678-1234-5678-1234-567812345678"),
            date_=date(2027, 1, 1),
            name="New Year's Day",
        )
        await uow.holidays.add(holiday1)
        await uow.holidays.add(holiday2)

        await uow.commit()

    list_uc = ListHolidaysUseCase(sqlalchemy_uow)

    cmd = ListHolidaysCommand(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        year=2027,
        month=1,
    )

    holidays = await list_uc.execute(cmd)

    assert len(holidays) == 1
    assert holidays[0].name == "New Year's Day"
    assert holidays[0].date == date(2027, 1, 1)


@pytest.mark.asyncio
async def test__list_all_holidays_use_case(sqlalchemy_uow, add_business_in_db):
    # Add holidays for the same business in different years and months
    async with sqlalchemy_uow as uow:
        holiday1 = Holiday.create(
            business_id=UUID("12345678-1234-5678-1234-567812345678"),
            date_=date(2026, 1, 1),
            name="New Year's Day",
        )
        holiday2 = Holiday.create(
            business_id=UUID("12345678-1234-5678-1234-567812345678"),
            date_=date(2027, 1, 1),
            name="New Year's Day",
        )
        holiday3 = Holiday.create(
            business_id=UUID("12345678-1234-5678-1234-567812345678"),
            date_=date(2027, 2, 14),
            name="Valentine's Day",
        )
        await uow.holidays.add(holiday1)
        await uow.holidays.add(holiday2)
        await uow.holidays.add(holiday3)
        await uow.commit()

    list_uc = ListHolidaysUseCase(sqlalchemy_uow)

    cmd = ListHolidaysCommand(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
    )

    holidays = await list_uc.execute(cmd)

    assert len(holidays) == 3
    assert holidays[0].name == "New Year's Day"
    assert holidays[0].date == date(2026, 1, 1)
    assert holidays[1].name == "New Year's Day"
    assert holidays[1].date == date(2027, 1, 1)
    assert holidays[2].name == "Valentine's Day"
    assert holidays[2].date == date(2027, 2, 14)


@pytest.mark.asyncio
async def test__delete_holiday(sqlalchemy_uow, add_business_and_holiday_in_db):
    delete_uc = DeleteHolidayUseCase(sqlalchemy_uow)

    cmd = DeleteHolidayCommand(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        date=date(2026, 1, 1),
    )

    await delete_uc.execute(cmd)

    # Assert DB state using a fresh UoW
    async with sqlalchemy_uow as uow:
        reloaded = await uow.holidays.get_by_business_and_date(
            business_id=UUID("12345678-1234-5678-1234-567812345678"),
            date_=date(2026, 1, 1),
        )
        assert reloaded is None


@pytest.mark.asyncio
async def test__get_holiday_by_business_and_date(
    sqlalchemy_uow, add_business_and_holiday_in_db
):
    get_uc = GetHolidayByDateUseCase(sqlalchemy_uow)

    cmd = GetHolidayByDateCommand(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        date=date(2026, 1, 1),
    )

    holiday = await get_uc.execute(cmd)

    assert holiday is not None
    assert holiday.name == "New Year's Day"
    assert holiday.date == date(2026, 1, 1)
