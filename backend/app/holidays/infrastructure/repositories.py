from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.holidays.application.ports import HolidayRepositoryPort
from app.holidays.domain.entities import Holiday
from app.holidays.infrastructure.orm import HolidayModel


class SqlAlchemyHolidayRepository(HolidayRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, holiday: Holiday) -> None:
        holiday_model = HolidayModel.from_entity(holiday)
        self.session.add(holiday_model)
        await self.session.flush()

    async def get_by_business_and_date(
        self, business_id: UUID, date_: date
    ) -> Holiday | None:
        result = await self.session.execute(
            select(HolidayModel).where(
                HolidayModel.business_id == business_id, HolidayModel.date == date_
            )
        )
        holiday_model = result.scalar_one_or_none()
        if holiday_model is None:
            return None
        return holiday_model.to_entity()

    async def get_by_business_and_id(
        self, business_id: UUID, holiday_id: UUID
    ) -> Holiday | None:
        result = await self.session.execute(
            select(HolidayModel).where(
                HolidayModel.business_id == business_id, HolidayModel.id == holiday_id
            )
        )
        holiday_model = result.scalar_one_or_none()
        if holiday_model is None:
            return None
        return holiday_model.to_entity()

    async def list_by_business(
        self, business_id: UUID, year: int | None = None, month: int | None = None
    ) -> Sequence[Holiday]:
        stmt = select(HolidayModel).where(HolidayModel.business_id == business_id)
        if year is not None:
            stmt = stmt.where(extract("year", HolidayModel.date) == year)
        if month is not None:
            stmt = stmt.where(extract("month", HolidayModel.date) == month)
        result = await self.session.execute(stmt)
        holiday_models = result.scalars().all()
        return [hm.to_entity() for hm in holiday_models]

    async def delete_by_business_and_date(self, business_id: UUID, date_: date) -> None:
        stmt = select(HolidayModel).where(
            HolidayModel.business_id == business_id, HolidayModel.date == date_
        )
        result = await self.session.execute(stmt)
        holiday_model = result.scalar_one_or_none()
        if holiday_model:
            await self.session.delete(holiday_model)

    async def update(self, holiday: Holiday) -> None:
        stmt = select(HolidayModel).where(
            HolidayModel.business_id == holiday.business_id,
            HolidayModel.id == holiday.id,
        )
        result = await self.session.execute(stmt)
        holiday_model = result.scalar_one_or_none()
        if not holiday_model:
            return None
        holiday_model.name = holiday.name

        await self.session.flush()

    async def list_for_period(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Sequence[Holiday]:
        stmt = select(HolidayModel).where(
            HolidayModel.business_id == business_id,
            HolidayModel.date >= start_date,
            HolidayModel.date <= end_date,
        )
        result = await self.session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]
