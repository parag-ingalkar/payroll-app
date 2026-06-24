from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from app.businesses.application.commands import (
    CreateBusinessCommand,
    ReplaceWeeklyOffRulesCommand,
    UpdateBusinessCommand,
)
from app.businesses.domain.entities import Business, WeeklyOffRule
from app.businesses.domain.exceptions import (
    BusinessNotFoundError,
    DuplicateBusinessError,
)
from app.core.uow import UnitOfWorkPort


@dataclass(slots=True)
class CreateBusinessUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: CreateBusinessCommand) -> Business:
        business = Business.create(
            owner_id=cmd.owner_id,
            name=cmd.name,
            default_salary_basis=cmd.default_salary_basis,
            payroll_start_day=cmd.payroll_start_day,
            default_wage_type=cmd.default_wage_type,
            default_working_hours_per_day=cmd.default_working_hours_per_day,
            default_overtime_multiplier=cmd.default_overtime_multiplier,
            weekly_off_rules=[
                WeeklyOffRule(weekday=rule.weekday) for rule in cmd.weekly_off_rules
            ],
        )

        async with self.uow as uow:
            existing = await uow.businesses.get_by_owner_and_slug(
                owner_id=cmd.owner_id, slug=business.slug
            )
            if existing:
                raise DuplicateBusinessError(
                    f"A business with the name '{cmd.name}' already exists for this owner."
                )

            await uow.businesses.add(business)
            await uow.commit()

            return business


@dataclass(slots=True)
class ListBusinessesUseCase:
    uow: UnitOfWorkPort

    async def execute(self, owner_id: str) -> Sequence[Business]:
        async with self.uow as uow:
            businesses = await uow.businesses.list_by_owner(owner_id=owner_id)
            return businesses


@dataclass(slots=True)
class GetBusinessUseCase:
    uow: UnitOfWorkPort

    async def execute(self, business_id: UUID, owner_id: str) -> Business:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=business_id, owner_id=owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID '{business_id}' not found."
                )
            return business


@dataclass(slots=True)
class UpdateBusinessUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: UpdateBusinessCommand) -> Business:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID '{cmd.business_id}' not found."
                )

            business.update(
                new_name=cmd.name,
                default_wage_type=cmd.default_wage_type,
                default_working_hours_per_day=cmd.default_working_hours_per_day,
                default_overtime_multiplier=cmd.default_overtime_multiplier,
                default_salary_basis=cmd.default_salary_basis,
                payroll_start_day=cmd.payroll_start_day,
            )

            await uow.businesses.update(business)
            await uow.commit()

            return business


@dataclass(slots=True)
class GetWeeklyOffRulesUseCase:
    uow: UnitOfWorkPort

    async def execute(
        self, business_id: UUID, owner_id: str
    ) -> Sequence[WeeklyOffRule]:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=business_id, owner_id=owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID '{business_id}' not found."
                )
            return business.weekly_off_rules


@dataclass(slots=True)
class ReplaceWeeklyOffRulesUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: ReplaceWeeklyOffRulesCommand) -> Business:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=cmd.business_id, owner_id=cmd.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID '{cmd.business_id}' not found."
                )

            new_rules = [
                WeeklyOffRule(weekday=rule.weekday) for rule in cmd.weekly_off_rules
            ]
            business.replace_weekly_off_rules(new_rules)

            await uow.businesses.replace_weekly_off_rules(
                business_id=cmd.business_id, new_rules=business.weekly_off_rules
            )
            await uow.commit()

            return business


@dataclass(slots=True)
class DeleteBusinessUseCase:
    uow: UnitOfWorkPort

    async def execute(self, business_id: UUID, owner_id: str) -> None:
        async with self.uow as uow:
            business = await uow.businesses.get_by_id_and_owner(
                business_id=business_id, owner_id=owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID '{business_id}' not found."
                )

            await uow.businesses.delete(business)
            await uow.commit()
