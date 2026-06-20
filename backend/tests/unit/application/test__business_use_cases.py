from decimal import Decimal
from uuid import uuid4

import pytest

from app.business.domain.entities import WageType, Weekday
from app.business.domain.exceptions import (
    BusinessNotFoundError,
    DuplicateBusinessError,
    InvalidWeeklyOffRulesError,
)
from app.business.application.commands import (
    CreateBusinessCommand,
    ReplaceWeeklyOffRulesCommand,
    UpdateBusinessCommand,
    WeeklyOffRuleInput,
)
from app.business.application.use_cases import (
    CreateBusinessUseCase,
    DeleteBusinessUseCase,
    GetBusinessUseCase,
    GetWeeklyOffRulesUseCase,
    ReplaceWeeklyOffRulesUseCase,
    UpdateBusinessUseCase,
)


@pytest.mark.asyncio
async def test__create_business_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    use_case = CreateBusinessUseCase(in_memory_uow)

    weekly_off_rules = [
        WeeklyOffRuleInput(weekday=Weekday.MONDAY, week_of_month=None),
        WeeklyOffRuleInput(weekday=Weekday.WEDNESDAY, week_of_month=1),
    ]

    cmd = CreateBusinessCommand(
        owner_id=business_defaults["owner_id"],
        name="New Business",
        default_wage_type=business_defaults["default_wage_type"],
        default_working_hours_per_day=business_defaults[
            "default_working_hours_per_day"
        ],
        default_overtime_multiplier=business_defaults["default_overtime_multiplier"],
        payroll_start_day=business_defaults["payroll_start_day"],
        weekly_off_rules=weekly_off_rules,
    )

    business = await use_case.execute(cmd)

    assert business.id is not None
    assert business.owner_id == business_defaults["owner_id"]
    assert business.name == "New Business"
    assert in_memory_uow.committed is True
    assert len(in_memory_business_repo._items) == 2


@pytest.mark.asyncio
async def test__create_business_duplicate_name_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    use_case = CreateBusinessUseCase(in_memory_uow)

    cmd = CreateBusinessCommand(
        owner_id=business_defaults["owner_id"],
        name="  " + business_defaults["name"].lower() + "  ",
        default_wage_type=business_defaults["default_wage_type"],
        default_working_hours_per_day=business_defaults[
            "default_working_hours_per_day"
        ],
        default_overtime_multiplier=business_defaults["default_overtime_multiplier"],
        payroll_start_day=business_defaults["payroll_start_day"],
        weekly_off_rules=[],
    )

    with pytest.raises(DuplicateBusinessError):
        await use_case.execute(cmd)

    assert in_memory_uow.committed is False
    assert len(in_memory_business_repo._items) == 1


@pytest.mark.asyncio
async def test__update_business_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    use_case = UpdateBusinessUseCase(in_memory_uow)

    cmd = UpdateBusinessCommand(
        business_id=in_memory_business_repo._items[0].id,
        owner_id=business_defaults["owner_id"],
        name="Updated Business Name",
        default_wage_type=WageType.HOURLY,
        default_working_hours_per_day=Decimal("7.5"),
        default_overtime_multiplier=Decimal("1.75"),
        payroll_start_day=15,
    )

    business = await use_case.execute(cmd)

    assert business.name == "Updated Business Name"
    assert business.default_wage_type == WageType.HOURLY
    assert business.default_working_hours_per_day == Decimal("7.5")
    assert business.default_overtime_multiplier == Decimal("1.75")
    assert business.payroll_start_day == 15
    assert in_memory_uow.committed is True
    assert len(in_memory_business_repo._items) == 1


@pytest.mark.asyncio
async def test__update_business_not_found_raises_error(
    business_defaults,
    in_memory_uow,
):
    use_case = UpdateBusinessUseCase(in_memory_uow)

    cmd = UpdateBusinessCommand(
        business_id=uuid4(),
        owner_id=business_defaults["owner_id"],
        name="Updated Business Name",
        default_wage_type=WageType.HOURLY,
        default_working_hours_per_day=Decimal("7.5"),
        default_overtime_multiplier=Decimal("1.75"),
        payroll_start_day=15,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)

    assert in_memory_uow.committed is False


@pytest.mark.asyncio
async def test__update_business_not_by_owner_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    use_case = UpdateBusinessUseCase(in_memory_uow)

    cmd = UpdateBusinessCommand(
        business_id=in_memory_business_repo._items[0].id,
        owner_id="some-other-owner",
        name="Updated Business Name",
        default_wage_type=WageType.HOURLY,
        default_working_hours_per_day=Decimal("7.5"),
        default_overtime_multiplier=Decimal("1.75"),
        payroll_start_day=15,
    )

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(cmd)

    assert in_memory_uow.committed is False


@pytest.mark.asyncio
async def test__get_business_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    use_case = GetBusinessUseCase(in_memory_uow)

    business = await use_case.execute(
        business_id=in_memory_business_repo._items[0].id,
        owner_id=business_defaults["owner_id"],
    )

    assert business is not None
    assert business.id == in_memory_business_repo._items[0].id
    assert business.owner_id == business_defaults["owner_id"]


@pytest.mark.asyncio
async def test__get_business_not_found_raises_error(
    business_defaults,
    in_memory_uow,
):
    use_case = GetBusinessUseCase(in_memory_uow)

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(
            business_id=uuid4(), owner_id=business_defaults["owner_id"]
        )


@pytest.mark.asyncio
async def test__delete_business_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    use_case = DeleteBusinessUseCase(in_memory_uow)

    await use_case.execute(
        business_id=in_memory_business_repo._items[0].id,
        owner_id=business_defaults["owner_id"],
    )

    assert in_memory_uow.committed is True
    assert len(in_memory_business_repo._items) == 0


@pytest.mark.asyncio
async def test__delete_business_not_found_raises_error(
    business_defaults,
    in_memory_uow,
):
    use_case = DeleteBusinessUseCase(in_memory_uow)

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(
            business_id=uuid4(), owner_id=business_defaults["owner_id"]
        )

    assert in_memory_uow.committed is False
    assert len(in_memory_uow.businesses._items) == 1


@pytest.mark.asyncio
async def test__delete_business_not_by_owner_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    use_case = DeleteBusinessUseCase(in_memory_uow)

    with pytest.raises(BusinessNotFoundError):
        await use_case.execute(
            business_id=in_memory_business_repo._items[0].id,
            owner_id="some-other-owner",
        )

    assert in_memory_uow.committed is False
    assert len(in_memory_uow.businesses._items) == 1


@pytest.mark.asyncio
async def test__get_weekly_off_rules_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    use_case = GetWeeklyOffRulesUseCase(in_memory_uow)

    weekly_off_rules = await use_case.execute(
        business_id=in_memory_business_repo._items[0].id,
        owner_id=business_defaults["owner_id"],
    )

    assert weekly_off_rules is not None
    for rule in weekly_off_rules:
        assert rule in in_memory_business_repo._items[0].weekly_off_rules


@pytest.mark.asyncio
async def test__replace_weekly_off_rules_happy_path(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    use_case = ReplaceWeeklyOffRulesUseCase(in_memory_uow)

    new_rules = [
        WeeklyOffRuleInput(weekday=Weekday.MONDAY, week_of_month=None),
        WeeklyOffRuleInput(weekday=Weekday.WEDNESDAY, week_of_month=1),
    ]

    business = await use_case.execute(
        ReplaceWeeklyOffRulesCommand(
            business_id=in_memory_business_repo._items[0].id,
            owner_id=business_defaults["owner_id"],
            weekly_off_rules=new_rules,
        )
    )

    assert {
        (rule.weekday, rule.week_of_month) for rule in business.weekly_off_rules
    } == {(rule.weekday, rule.week_of_month) for rule in new_rules}


@pytest.mark.asyncio
async def test__replace_weekly_off_rules_with_invalid_rules_raises_error(
    business_defaults,
    in_memory_uow,
    in_memory_business_repo,
):
    use_case = ReplaceWeeklyOffRulesUseCase(in_memory_uow)

    new_rules = [
        WeeklyOffRuleInput(weekday=Weekday.MONDAY, week_of_month=None),
        WeeklyOffRuleInput(weekday=Weekday.MONDAY, week_of_month=None),
    ]

    with pytest.raises(InvalidWeeklyOffRulesError):
        await use_case.execute(
            ReplaceWeeklyOffRulesCommand(
                business_id=in_memory_business_repo._items[0].id,
                owner_id=business_defaults["owner_id"],
                weekly_off_rules=new_rules,
            )
        )
