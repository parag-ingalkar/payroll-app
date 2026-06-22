from decimal import Decimal

import pytest

from app.business.domain.entities import (
    Business,
    WageType,
    Weekday,
    WeeklyOffRule,
)
from app.business.domain.exceptions import InvalidWeeklyOffRulesError
from app.business.domain.value_objects import SalaryBasis


def test__business_creation_with_valid_weekly_off_rules(business_defaults):
    business = Business.create(**business_defaults)

    assert len(business.weekly_off_rules) == 2
    assert business.weekly_off_rules[0].weekday == Weekday.MONDAY
    assert business.weekly_off_rules[0].week_of_month is None
    assert business.weekly_off_rules[1].weekday == Weekday.TUESDAY
    assert business.weekly_off_rules[1].week_of_month == 2


def test__rename_business(business_defaults):
    business = Business.create(**business_defaults)

    business.rename("Updated Business Name")

    assert business.name == "Updated Business Name"


def test__update_business_defaults(business_defaults):
    business = Business.create(**business_defaults)

    business.update_defaults(
        default_wage_type=WageType.MONTHLY,
        default_working_hours_per_day=Decimal("7.5"),
        default_overtime_multiplier=Decimal("2.0"),
        payroll_start_day=15,
    )

    assert business.default_wage_type == WageType.MONTHLY
    assert business.default_working_hours_per_day == Decimal("7.5")
    assert business.default_overtime_multiplier == Decimal("2.0")
    assert business.payroll_start_day == 15


def test__weekly_off_rules_with_duplicates_is_invalid(business_defaults):
    business = Business.create(**business_defaults)

    rules = [
        WeeklyOffRule(weekday=Weekday.MONDAY, week_of_month=None),
        WeeklyOffRule(weekday=Weekday.MONDAY, week_of_month=None),
    ]

    with pytest.raises(InvalidWeeklyOffRulesError):
        business.replace_weekly_off_rules(rules)


def test__replace_weekly_off_rules_with_valid_rules(business_defaults):
    business = Business.create(**business_defaults)

    rules = [
        WeeklyOffRule(weekday=Weekday.SUNDAY, week_of_month=None),
        WeeklyOffRule(weekday=Weekday.SATURDAY, week_of_month=2),
    ]

    business.replace_weekly_off_rules(rules)

    assert len(business.weekly_off_rules) == 2
    assert business.weekly_off_rules[0].weekday == Weekday.SUNDAY
    assert business.weekly_off_rules[0].week_of_month is None
    assert business.weekly_off_rules[1].weekday == Weekday.SATURDAY
    assert business.weekly_off_rules[1].week_of_month == 2


def test__weekly_off_rules_every_sunday_plus_first_sunday_is_invalid(
    business_defaults,
):
    business = Business.create(**business_defaults)

    rules = [
        WeeklyOffRule(weekday=Weekday.SUNDAY, week_of_month=None),
        WeeklyOffRule(weekday=Weekday.SUNDAY, week_of_month=1),
    ]

    with pytest.raises(InvalidWeeklyOffRulesError):
        business.replace_weekly_off_rules(rules)


def test__default_update_with_partial_fields(business_defaults):
    business = Business.create(**business_defaults)

    business.update_defaults(
        default_working_hours_per_day=Decimal("7.0"),
    )

    assert business.default_wage_type == WageType.HOURLY
    assert business.default_working_hours_per_day == Decimal("7.0")
    assert business.default_overtime_multiplier == Decimal("1.5")
    assert business.payroll_start_day == 1


def test__invalid_business_name_on_creation():
    with pytest.raises(ValueError):
        Business.create(
            owner_id="owner-1",
            name="   ",  # Invalid name (only whitespace)
            default_wage_type=WageType.HOURLY,
            default_working_hours_per_day=Decimal("8.0"),
            default_overtime_multiplier=Decimal("1.5"),
            default_salary_basis=SalaryBasis.WORKING_26_DAYS,
            payroll_start_day=1,
            weekly_off_rules=[],
        )


def test__invalid_defaults_during_creation():
    # invalid working hours < 0
    with pytest.raises(ValueError):
        Business.create(
            owner_id="owner-1",
            name="Test Business",
            default_wage_type=WageType.HOURLY,
            default_working_hours_per_day=Decimal("-1"),
            default_overtime_multiplier=Decimal("1.5"),
            default_salary_basis=SalaryBasis.WORKING_26_DAYS,
            payroll_start_day=1,
            weekly_off_rules=[],
        )

    # invalid working hours > 24
    with pytest.raises(ValueError):
        Business.create(
            owner_id="owner-1",
            name="Test Business",
            default_wage_type=WageType.HOURLY,
            default_working_hours_per_day=Decimal("25"),
            default_overtime_multiplier=Decimal("1.5"),
            default_salary_basis=SalaryBasis.WORKING_26_DAYS,
            payroll_start_day=1,
            weekly_off_rules=[],
        )

    # invalid overtime multiplier < 1
    with pytest.raises(ValueError):
        Business.create(
            owner_id="owner-1",
            name="Test Business",
            default_wage_type=WageType.HOURLY,
            default_working_hours_per_day=Decimal("8.0"),
            default_overtime_multiplier=Decimal("0.5"),
            default_salary_basis=SalaryBasis.WORKING_26_DAYS,
            payroll_start_day=1,
            weekly_off_rules=[],
        )


def test__invalid_default_updates(business_defaults):
    business = Business.create(**business_defaults)

    with pytest.raises(ValueError):
        business.update_defaults(default_working_hours_per_day=Decimal("-1"))

    with pytest.raises(ValueError):
        business.update_defaults(default_working_hours_per_day=Decimal("25"))

    with pytest.raises(ValueError):
        business.update_defaults(default_overtime_multiplier=Decimal("0.5"))
