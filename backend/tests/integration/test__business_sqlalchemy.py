# tests/integration/test__business_use_cases_integration.py

from decimal import Decimal
import pytest

from app.business.domain.entities import WageType, Weekday
from app.business.domain.exceptions import DuplicateBusinessError, BusinessNotFoundError
from app.business.application.commands import (
    CreateBusinessCommand,
    ReplaceWeeklyOffRulesCommand,
    UpdateBusinessCommand,
    WeeklyOffRuleInput,
)
from app.business.application.use_cases import (
    CreateBusinessUseCase,
    GetBusinessUseCase,
    ReplaceWeeklyOffRulesUseCase,
    UpdateBusinessUseCase,
    DeleteBusinessUseCase,
)


@pytest.mark.asyncio
async def test__create_and_get_business_integration(sqlalchemy_business_uow):
    create_uc = CreateBusinessUseCase(sqlalchemy_business_uow)
    get_uc = GetBusinessUseCase(sqlalchemy_business_uow)

    cmd = CreateBusinessCommand(
        owner_id="owner-int-1",
        name="Integration Biz",
        default_wage_type=WageType.HOURLY,
        default_working_hours_per_day=Decimal("8.0"),
        default_overtime_multiplier=Decimal("1.5"),
        payroll_start_day=1,
        weekly_off_rules=[
            WeeklyOffRuleInput(weekday=Weekday.MONDAY, week_of_month=2),
            WeeklyOffRuleInput(weekday=Weekday.THURSDAY, week_of_month=None),
        ],
    )

    created = await create_uc.execute(cmd)
    fetched = await get_uc.execute(created.id, "owner-int-1")

    assert fetched.id == created.id
    assert fetched.name == "Integration Biz"
    assert len(fetched.weekly_off_rules) == 2
    assert fetched.weekly_off_rules[0].weekday == Weekday.MONDAY
    assert fetched.weekly_off_rules[0].week_of_month == 2
    assert fetched.weekly_off_rules[1].weekday == Weekday.THURSDAY
    assert fetched.weekly_off_rules[1].week_of_month is None


@pytest.mark.asyncio
async def test__update_business_integration(sqlalchemy_business_uow):
    create_uc = CreateBusinessUseCase(sqlalchemy_business_uow)
    update_uc = UpdateBusinessUseCase(sqlalchemy_business_uow)
    get_uc = GetBusinessUseCase(sqlalchemy_business_uow)

    # create
    created = await create_uc.execute(
        CreateBusinessCommand(
            owner_id="owner-int-2",
            name="Old Name",
            default_wage_type=WageType.HOURLY,
            default_working_hours_per_day=Decimal("8.0"),
            default_overtime_multiplier=Decimal("1.5"),
            payroll_start_day=1,
            weekly_off_rules=[],
        )
    )

    # update
    await update_uc.execute(
        UpdateBusinessCommand(
            business_id=created.id,
            owner_id="owner-int-2",
            name="New Name",
            default_wage_type=None,
            default_working_hours_per_day=None,
            default_overtime_multiplier=None,
            payroll_start_day=None,
        )
    )

    # verify persisted
    fetched = await get_uc.execute(created.id, "owner-int-2")
    assert fetched.name == "New Name"


@pytest.mark.asyncio
async def test__replace_business_weekly_off_rules_integration(sqlalchemy_business_uow):
    create_uc = CreateBusinessUseCase(sqlalchemy_business_uow)
    replace_weekly_off_rules_uc = ReplaceWeeklyOffRulesUseCase(sqlalchemy_business_uow)
    get_uc = GetBusinessUseCase(sqlalchemy_business_uow)

    create_cmd = CreateBusinessCommand(
        owner_id="owner-int-1",
        name="Integration Biz",
        default_wage_type=WageType.HOURLY,
        default_working_hours_per_day=Decimal("8.0"),
        default_overtime_multiplier=Decimal("1.5"),
        payroll_start_day=1,
        weekly_off_rules=[
            WeeklyOffRuleInput(weekday=Weekday.MONDAY, week_of_month=2),
            WeeklyOffRuleInput(weekday=Weekday.THURSDAY, week_of_month=None),
        ],
    )

    created = await create_uc.execute(create_cmd)
    assert len(created.weekly_off_rules) == 2

    replace_weekly_off_rules_cmd = ReplaceWeeklyOffRulesCommand(
        business_id=created.id,
        owner_id="owner-int-1",
        weekly_off_rules=[
            WeeklyOffRuleInput(weekday=Weekday.TUESDAY, week_of_month=1),
            WeeklyOffRuleInput(weekday=Weekday.FRIDAY, week_of_month=None),
        ],
    )

    await replace_weekly_off_rules_uc.execute(replace_weekly_off_rules_cmd)

    fetched = await get_uc.execute(created.id, "owner-int-1")
    weekdays = [rule.weekday for rule in fetched.weekly_off_rules]
    print(weekdays)
    assert len(fetched.weekly_off_rules) == 2
    assert fetched.weekly_off_rules[0].weekday == Weekday.TUESDAY
    assert fetched.weekly_off_rules[0].week_of_month == 1
    assert fetched.weekly_off_rules[1].weekday == Weekday.FRIDAY
    assert fetched.weekly_off_rules[1].week_of_month is None


@pytest.mark.asyncio
async def test__delete_business_integration(sqlalchemy_business_uow):
    create_uc = CreateBusinessUseCase(sqlalchemy_business_uow)
    delete_uc = DeleteBusinessUseCase(sqlalchemy_business_uow)
    get_uc = GetBusinessUseCase(sqlalchemy_business_uow)

    created = await create_uc.execute(
        CreateBusinessCommand(
            owner_id="owner-int-3",
            name="To Be Deleted",
            default_wage_type=WageType.HOURLY,
            default_working_hours_per_day=Decimal("8.0"),
            default_overtime_multiplier=Decimal("1.5"),
            payroll_start_day=1,
            weekly_off_rules=[],
        )
    )

    await delete_uc.execute(created.id, "owner-int-3")

    with pytest.raises(BusinessNotFoundError):
        await get_uc.execute(created.id, "owner-int-3")


@pytest.mark.asyncio
async def test__cannot_create_duplicate_business_integration(sqlalchemy_business_uow):
    create_uc = CreateBusinessUseCase(sqlalchemy_business_uow)

    await create_uc.execute(
        CreateBusinessCommand(
            owner_id="owner-int-4",
            name="Duplicate Biz",
            default_wage_type=WageType.HOURLY,
            default_working_hours_per_day=Decimal("8.0"),
            default_overtime_multiplier=Decimal("1.5"),
            payroll_start_day=1,
            weekly_off_rules=[],
        )
    )

    with pytest.raises(DuplicateBusinessError):
        await create_uc.execute(
            CreateBusinessCommand(
                owner_id="owner-int-4",
                name="Duplicate Biz",  # same name + owner
                default_wage_type=WageType.HOURLY,
                default_working_hours_per_day=Decimal("8.0"),
                default_overtime_multiplier=Decimal("1.5"),
                payroll_start_day=1,
                weekly_off_rules=[],
            )
        )
