from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.holidays.application.ports import HolidaysRepositoryPort
from app.holidays.domain.entities import Holiday
from app.holidays.infrastructure.models import HolidayModel


@dataclass
class SqlHolidaysRepository(HolidaysRepositoryPort):
    session: AsyncSession

    async def add(self, holiday: Holiday) -> None:
        holiday_model = HolidayModel.from_entity(holiday)
        self.session.add(holiday_model)
        await self.session.flush()  # Ensure the model is persisted and ID is generated

    async def get_by_business_and_date(
        self, business_id: UUID, holiday_date: date
    ) -> Holiday | None:
        stmt = select(HolidayModel).where(
            HolidayModel.business_id == business_id,
            HolidayModel.holiday_date == holiday_date,
        )
        result = await self.session.execute(stmt)
        holiday_model = result.scalar_one_or_none()
        return holiday_model.to_entity() if holiday_model else None

    async def list_by_business(
        self, business_id: UUID, year: int | None = None, month: int | None = None
    ) -> Sequence[Holiday]:
        stmt = select(HolidayModel).where(HolidayModel.business_id == business_id)

        if year is not None:
            stmt = stmt.where(extract("year", HolidayModel.holiday_date) == year)
        if month is not None:
            stmt = stmt.where(extract("month", HolidayModel.holiday_date) == month)

        result = await self.session.execute(stmt)
        holiday_models = result.scalars().all()
        return [holiday_model.to_entity() for holiday_model in holiday_models]

    async def delete_by_business(self, business_id: UUID, holiday_date: date) -> None:
        stmt = select(HolidayModel).where(
            HolidayModel.business_id == business_id,
            HolidayModel.holiday_date == holiday_date,
        )
        result = await self.session.execute(stmt)
        holiday_model = result.scalar_one_or_none()
        if holiday_model:
            await self.session.delete(holiday_model)
            await self.session.flush()  # Ensure the deletion is persisted

    async def update(self, holiday: Holiday) -> None:
        stmt = select(HolidayModel).where(
            HolidayModel.business_id == holiday.business_id,
            HolidayModel.holiday_date == holiday.holiday_date,
        )
        result = await self.session.execute(stmt)
        holiday_model = result.scalar_one_or_none()
        if holiday_model:
            holiday_model.holiday_name = holiday.holiday_name
            holiday_model.is_paid = holiday.is_paid
            await self.session.flush()  # Ensure the update is persisted

    async def list_for_period(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Sequence[Holiday]:
        stmt = select(HolidayModel).where(
            HolidayModel.business_id == business_id,
            HolidayModel.holiday_date >= start_date,
            HolidayModel.holiday_date <= end_date,
        )
        result = await self.session.execute(stmt)
        holiday_models = result.scalars().all()
        return [holiday_model.to_entity() for holiday_model in holiday_models]
