from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.business.application.ports import BusinessRepositoryPort
from app.business.domain.entities import Business
from app.business.infrastructure.orm import BusinessModel, BusinessWeeklyOffRuleModel
from app.business.infrastructure.mappers import (
    business_model_to_domain,
    business_domain_to_model,
    sync_business_identity_from_model,
)
from app.business.domain.value_objects import normalize_business_name_for_lookup


class SqlAlchemyBusinessRepository(BusinessRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, business: Business) -> None:
        model = business_domain_to_model(business)
        self._session.add(model)
        await self._session.flush()
        sync_business_identity_from_model(business, model)

    async def get_by_id_and_owner(
        self, business_id: UUID, owner_id: str
    ) -> Business | None:
        stmt = (
            select(BusinessModel)
            .options(selectinload(BusinessModel.weekly_off_rules))
            .where(
                BusinessModel.id == business_id,
                BusinessModel.owner_id == owner_id,
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return business_model_to_domain(model)

    async def list_by_owner(self, owner_id: str) -> Sequence[Business]:
        stmt = (
            select(BusinessModel)
            .options(selectinload(BusinessModel.weekly_off_rules))
            .where(BusinessModel.owner_id == owner_id)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [business_model_to_domain(m) for m in models]

    async def find_by_normalized_name(
        self,
        owner_id: str,
        normalized_name: str,
    ) -> Business | None:
        stmt = (
            select(BusinessModel)
            .options(selectinload(BusinessModel.weekly_off_rules))
            .where(
                BusinessModel.owner_id == owner_id,
                BusinessModel.normalized_name == normalized_name,
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return business_model_to_domain(model)

    async def find_by_owner_and_name(
        self,
        owner_id: str,
        name: str,
    ) -> Business | None:
        normalized_name = normalize_business_name_for_lookup(name)

        stmt = (
            select(BusinessModel)
            .options(selectinload(BusinessModel.weekly_off_rules))
            .where(
                BusinessModel.owner_id == owner_id,
                BusinessModel.normalized_name == normalized_name,
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return business_model_to_domain(model)

    async def delete(self, business: Business) -> None:
        # we only need the id + owner_id; load by id+owner and delete model
        stmt = select(BusinessModel).where(BusinessModel.id == business.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)

    async def update(self, business: Business) -> None:
        business_ = business_domain_to_model(business)
        stmt = (
            select(BusinessModel)
            .options(selectinload(BusinessModel.weekly_off_rules))
            .where(BusinessModel.id == business_.id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return

        model.owner_id = business_.owner_id
        model.name = business_.name
        model.normalized_name = business_.normalized_name
        model.default_wage_type = business_.default_wage_type
        model.default_working_hours_per_day = business_.default_working_hours_per_day
        model.default_overtime_multiplier = business_.default_overtime_multiplier
        model.payroll_start_day = business_.payroll_start_day

        # Replace weekly_off_rules
        model.weekly_off_rules.clear()
        for rule in business_.weekly_off_rules:
            model.weekly_off_rules.append(
                BusinessWeeklyOffRuleModel(
                    id=rule.id,
                    weekday=rule.weekday,
                    week_of_month=rule.week_of_month,
                )
            )
