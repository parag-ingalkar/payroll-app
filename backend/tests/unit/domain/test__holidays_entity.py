from uuid import UUID
from datetime import date

import pytest

from app.holidays.domain.entities import Holiday
from app.holidays.domain.exceptions import InvalidHolidayNameError


def test__create_holiday_with_valid_name():
    holiday = Holiday.create(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        date_=date(2024, 1, 1),
        name="New Year's Day",
    )
    assert holiday.name == "New Year's Day"
    assert holiday.date == date(2024, 1, 1)


def test__create_holiday_with_empty_name():
    holiday = Holiday.create(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        date_=date(2024, 1, 1),
        name="",
    )
    assert holiday.name is None
    assert holiday.date == date(2024, 1, 1)

    holiday = Holiday.create(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        date_=date(2024, 1, 1),
        name="   ",
    )
    assert holiday.name is None
    assert holiday.date == date(2024, 1, 1)

    holiday = Holiday.create(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        date_=date(2024, 1, 1),
        name=None,
    )
    assert holiday.name is None
    assert holiday.date == date(2024, 1, 1)


def test__rename_holiday_with_valid_name():
    holiday = Holiday.create(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        date_=date(2024, 1, 1),
        name="New Year's Day",
    )
    holiday.rename("New Year's Celebration")
    assert holiday.name == "New Year's Celebration"


def test__rename_holiday_with_invalid_name():
    holiday = Holiday.create(
        business_id=UUID("12345678-1234-5678-1234-567812345678"),
        date_=date(2024, 1, 1),
        name="New Year's Day",
    )
    with pytest.raises(InvalidHolidayNameError):
        holiday.rename("New Year's Day")
