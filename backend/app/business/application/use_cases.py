from collections.abc import Sequence
from uuid import UUID

from app.business.application.commands import (
    CreateBusinessCommand,
    ReplaceWeeklyOffRulesCommand,
    UpdateBusinessCommand,
)
from app.business.domain.entities import Business, WeeklyOffRule
from app.business.domain.exceptions import (
    BusinessNotFoundError,
    DuplicateBusinessError,
)
from app.business.domain.value_objects import normalize_business_name_for_lookup
from app.core.uow import UnitOfWorkPort


class CreateBusinessUseCase:
    def __init__(self, uow: UnitOfWorkPort):
        self._uow = uow

    async def execute(self, cmd: CreateBusinessCommand) -> Business:
        normalized_name = normalize_business_name_for_lookup(cmd.name)

        async with self._uow as uow:
            existing = await uow.businesses.find_by_normalized_name(
                owner_id=cmd.owner_id, normalized_name=normalized_name
            )
            if existing:
                raise DuplicateBusinessError(
                    f"A business with the name '{cmd.name}' already exists for this owner."
                )

            weekly_off_rules = [
                WeeklyOffRule(weekday=rule.weekday, week_of_month=rule.week_of_month)
                for rule in cmd.weekly_off_rules
            ]

            business = Business.create(
                owner_id=cmd.owner_id,
                name=cmd.name,
                default_wage_type=cmd.default_wage_type,
                default_working_hours_per_day=cmd.default_working_hours_per_day,
                default_overtime_multiplier=cmd.default_overtime_multiplier,
                default_salary_basis=cmd.default_salary_basis,
                payroll_start_day=cmd.payroll_start_day,
                weekly_off_rules=weekly_off_rules,
            )

            await uow.businesses.add(business)
            await uow.commit()

            return business


class ListBusinessesUseCase:
    def __init__(self, uow: UnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(self, owner_id: str) -> Sequence[Business]:
        async with self._uow as uow:
            businesses = await uow.businesses.list_by_owner(owner_id=owner_id)

            return sorted(businesses, key=lambda b: b.name.lower())


class GetBusinessUseCase:
    def __init__(self, uow: UnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(self, business_id: UUID, owner_id: str) -> Business:
        async with self._uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=business_id, owner_id=owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID {business_id} not found."
                )
            return business


class UpdateBusinessUseCase:
    def __init__(self, uow: UnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(self, cmd: UpdateBusinessCommand) -> Business:
        async with self._uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID {cmd.business_id} not found."
                )

            if cmd.name:
                normalized_name = normalize_business_name_for_lookup(cmd.name)
                existing = await uow.businesses.find_by_normalized_name(
                    owner_id=cmd.owner_id, normalized_name=normalized_name
                )
                if existing and existing.id != business.id:
                    raise DuplicateBusinessError(
                        f"A business with the name '{cmd.name}' already exists for this owner."
                    )
                business.rename(cmd.name)

            business.update_defaults(
                default_wage_type=cmd.default_wage_type,
                default_working_hours_per_day=cmd.default_working_hours_per_day,
                default_overtime_multiplier=cmd.default_overtime_multiplier,
                default_salary_basis=cmd.default_salary_basis,
                payroll_start_day=cmd.payroll_start_day,
            )

            await uow.businesses.update(business)
            await uow.commit()

            return business


class DeleteBusinessUseCase:
    def __init__(self, uow: UnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(self, business_id: UUID, owner_id: str) -> None:
        async with self._uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=business_id,
                owner_id=owner_id,
            )
            if business is None:
                raise BusinessNotFoundError(
                    "Business not found for this owner.",
                )

            await uow.businesses.delete(business)
            await uow.commit()


class GetWeeklyOffRulesUseCase:
    def __init__(self, uow: UnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(self, business_id: UUID, owner_id: str) -> list[WeeklyOffRule]:
        async with self._uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=business_id,
                owner_id=owner_id,
            )
            if business is None:
                raise BusinessNotFoundError(
                    "Business not found for this owner.",
                )
            return list(business.weekly_off_rules)


class ReplaceWeeklyOffRulesUseCase:
    def __init__(self, uow: UnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(self, cmd: ReplaceWeeklyOffRulesCommand) -> Business:
        async with self._uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id,
                owner_id=cmd.owner_id,
            )
            if business is None:
                raise BusinessNotFoundError(
                    "Business not found for this owner.",
                )

            rules = [
                WeeklyOffRule(
                    weekday=rule_input.weekday,
                    week_of_month=rule_input.week_of_month,
                )
                for rule_input in cmd.weekly_off_rules
            ]

            business.replace_weekly_off_rules(rules)

            await uow.businesses.update(business)
            await uow.commit()
            return business
