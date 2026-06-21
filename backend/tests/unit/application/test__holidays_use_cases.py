# tests/unit/application/test__holidays_use_cases.py
from datetime import date

import pytest

from app.holidays.domain.entities import Holiday
from app.holidays.domain.exceptions import (
    HolidayAlreadyExistsError,
    HolidayNotFoundError,
)
from app.holidays.application.commands import (
    CreateHolidayCommand,
    DeleteHolidayCommand,
    ListHolidaysCommand,
    RenameHolidayCommand,
)
from app.holidays.application.use_cases import (
    CreateHolidayUseCase,
    DeleteHolidayUseCase,
    ListHolidaysUseCase,
    RenameHolidayUseCase,
)


@pytest.mark.asyncio
async def test__create_holiday_use_case(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    cmd = CreateHolidayCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=date(2026, 1, 26),
        name="Republic Day",
    )

    use_case = CreateHolidayUseCase(uow=in_memory_uow)
    holiday = await use_case.execute(cmd)

    assert holiday.name == "Republic Day"
    assert holiday.date == date(2026, 1, 26)
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__list_holidays_use_case(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = ListHolidaysUseCase(uow=in_memory_uow)
    cmd = ListHolidaysCommand(
        business_id=business.id,
        owner_id=owner_id,
        year=2026,
        month=1,
    )

    holidays = await use_case.execute(cmd)

    assert len(holidays) == 1
    assert holidays[0].name == "New Year's Day"
    assert holidays[0].date == date(2026, 1, 1)


@pytest.mark.asyncio
async def test__rename_holiday_use_case(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = RenameHolidayUseCase(uow=in_memory_uow)
    cmd = RenameHolidayCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=date(2026, 1, 1),
        new_name="New Year's Celebration",
    )

    holiday = await use_case.execute(cmd)

    assert holiday.name == "New Year's Celebration"
    assert holiday.date == date(2026, 1, 1)
    assert in_memory_uow.committed is True


@pytest.mark.asyncio
async def test__rename_holiday_use_case_with_non_existent_holiday(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = RenameHolidayUseCase(uow=in_memory_uow)
    cmd = RenameHolidayCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=date(2026, 2, 1),
        new_name="Some Holiday",
    )

    with pytest.raises(HolidayNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__create_holiday_use_case_with_existing_holiday(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = CreateHolidayUseCase(uow=in_memory_uow)
    cmd = CreateHolidayCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=date(2026, 1, 1),
        name="Duplicate Holiday",
    )

    with pytest.raises(HolidayAlreadyExistsError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test__list_multiple_holidays_use_case(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_holiday_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    # Add another holiday for the same business
    another_holiday = Holiday.create(
        business_id=business.id,
        date_=date(2026, 1, 26),
        name="Republic Day",
    )
    await in_memory_holiday_repo.add(another_holiday)

    use_case = ListHolidaysUseCase(uow=in_memory_uow)
    cmd = ListHolidaysCommand(
        business_id=business.id,
        owner_id=owner_id,
        year=2026,
        month=1,
    )

    holidays = await use_case.execute(cmd)

    assert len(holidays) == 2
    assert holidays[0].name == "New Year's Day"
    assert holidays[0].date == date(2026, 1, 1)
    assert holidays[1].name == "Republic Day"
    assert holidays[1].date == date(2026, 1, 26)


@pytest.mark.asyncio
async def test__list_holidays_by_month_use_case(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_holiday_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    another_holiday = Holiday.create(
        business_id=business.id,
        date_=date(2026, 2, 1),
        name="Some February Holiday",
    )
    await in_memory_holiday_repo.add(another_holiday)

    use_case = ListHolidaysUseCase(uow=in_memory_uow)
    cmd = ListHolidaysCommand(
        business_id=business.id,
        owner_id=owner_id,
        year=2026,
        month=2,
    )

    holidays = await use_case.execute(cmd)

    assert len(holidays) == 1
    assert holidays[0].name == "Some February Holiday"
    assert holidays[0].date == date(2026, 2, 1)


@pytest.mark.asyncio
async def test__list_holidays_by_year_use_case(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_holiday_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    another_holiday = Holiday.create(
        business_id=business.id,
        date_=date(2027, 1, 1),
        name="Some January Holiday",
    )
    await in_memory_holiday_repo.add(another_holiday)

    use_case = ListHolidaysUseCase(uow=in_memory_uow)
    cmd = ListHolidaysCommand(
        business_id=business.id,
        owner_id=owner_id,
        year=2027,
    )

    holidays = await use_case.execute(cmd)

    assert len(holidays) == 1
    assert holidays[0].name == "Some January Holiday"
    assert holidays[0].date == date(2027, 1, 1)


@pytest.mark.asyncio
async def test__list_all_holidays_use_case(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_holiday_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    other_holiday = Holiday.create(
        business_id=business.id,
        date_=date(2027, 1, 1),
        name="Some January Holiday",
    )
    await in_memory_holiday_repo.add(other_holiday)

    another_holiday = Holiday.create(
        business_id=business.id,
        date_=date(2027, 2, 1),
        name="Some February Holiday",
    )
    await in_memory_holiday_repo.add(another_holiday)

    use_case = ListHolidaysUseCase(uow=in_memory_uow)
    cmd = ListHolidaysCommand(
        business_id=business.id,
        owner_id=owner_id,
    )

    holidays = await use_case.execute(cmd)

    assert len(holidays) == 3
    assert holidays[0].name == "New Year's Day"
    assert holidays[0].date == date(2026, 1, 1)
    assert holidays[1].name == "Some January Holiday"
    assert holidays[1].date == date(2027, 1, 1)
    assert holidays[2].name == "Some February Holiday"
    assert holidays[2].date == date(2027, 2, 1)


@pytest.mark.asyncio
async def test__delete_holiday_use_case(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
    in_memory_holiday_repo,
):
    business = in_memory_business_repo._items[0]
    owner_id = business_defaults["owner_id"]

    use_case = DeleteHolidayUseCase(uow=in_memory_uow)
    cmd = DeleteHolidayCommand(
        business_id=business.id,
        owner_id=owner_id,
        date=date(2026, 1, 1),
    )

    await use_case.execute(cmd)

    assert in_memory_uow.committed is True
    holidays = await in_memory_holiday_repo.list_by_business(business_id=business.id)
    assert len(holidays) == 0
