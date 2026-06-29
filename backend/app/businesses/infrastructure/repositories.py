from collections.abc import Sequence
from uuid import UUID
from app.businesses.domain.value_objects import BusinessPayrollConfiguration
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.businesses.domain.entities import Business, WeeklyOffRule
from app.businesses.infrastructure.models import BusinessModel, WeeklyOffRuleModel

from app.businesses.application.ports import BusinessRepositoryPort


class SqlBusinessRepository(BusinessRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, business: Business) -> None:
        model = BusinessModel.from_entity(business)
        self.session.add(model)
        await self.session.flush()  # Ensure the model is persisted and ID is generated

    async def get_by_id_and_owner(
        self, business_id: UUID, owner_id: str
    ) -> Business | None:
        result = await self.session.execute(
            select(BusinessModel)
            .where(BusinessModel.id == str(business_id))
            .where(BusinessModel.owner_id == owner_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_owner_and_slug(self, owner_id: str, slug: str) -> Business | None:
        result = await self.session.execute(
            select(BusinessModel)
            .where(BusinessModel.owner_id == owner_id)
            .where(BusinessModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list_by_owner(self, owner_id: str) -> Sequence[Business]:
        result = await self.session.execute(
            select(BusinessModel).where(BusinessModel.owner_id == owner_id)
        )
        models = result.scalars().all()
        return [model.to_entity() for model in models]

    async def update(self, business: Business) -> None:
        model = BusinessModel.from_entity(business)
        await self.session.merge(model)
        await self.session.flush()

    async def delete(self, business: Business) -> None:
        model = await self.session.get(BusinessModel, business.id)
        if model is None:
            return
        await self.session.delete(model)

    async def replace_weekly_off_rules(
        self, business_id: UUID, new_rules: Sequence[WeeklyOffRule]
    ) -> None:
        # 1. Delete existing rules in DB for this business
        await self.session.execute(
            delete(WeeklyOffRuleModel).where(
                WeeklyOffRuleModel.business_id == business_id
            )
        )
        await self.session.flush()  # ensure they are gone

        # 2. Insert new rules
        for rule in new_rules:
            self.session.add(
                WeeklyOffRuleModel(
                    business_id=business_id,
                    weekday=rule.weekday,
                )
            )

    async def get_business_payroll_configuration(
        self,
        *,
        business_id: UUID,
    ) -> BusinessPayrollConfiguration:
        # Fetch the business to get payroll_start_date
        result = await self.session.execute(
            select(BusinessModel).where(BusinessModel.id == str(business_id))
        )
        business_model = result.scalar_one_or_none()
        if not business_model:
            raise ValueError(f"Business with id {business_id} not found.")

        weekly_off_rules_models = business_model.weekly_off_rules

        weekly_off_rules = [
            WeeklyOffRule(weekday=rule_model.weekday, id=rule_model.id)
            for rule_model in weekly_off_rules_models
        ]

        return BusinessPayrollConfiguration(
            business_id=business_id,
            payroll_start_day=business_model.payroll_start_day,
            weekly_off_rules=weekly_off_rules,
        )
