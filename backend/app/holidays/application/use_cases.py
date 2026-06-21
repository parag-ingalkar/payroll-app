from dataclasses import dataclass
from typing import Sequence

from app.core.uow import UnitOfWorkPort
from app.holidays.domain.entities import Holiday
from app.holidays.domain.exceptions import (
    HolidayAlreadyExistsError,
    HolidayNotFoundError,
)
from app.holidays.application.commands import (
    CreateHolidayCommand,
    DeleteHolidayCommand,
    GetHolidayByDateCommand,
    ListHolidaysCommand,
    RenameHolidayCommand,
)


@dataclass
class CreateHolidayUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: CreateHolidayCommand) -> Holiday:
        async with self.uow as uow:
            holiday = await uow.holidays.get_by_business_and_date(
                business_id=cmd.business_id, date_=cmd.date
            )
            if holiday:
                raise HolidayAlreadyExistsError(
                    business_id=str(cmd.business_id),
                    date=str(cmd.date),
                )

            holiday = Holiday.create(
                business_id=cmd.business_id,
                date_=cmd.date,
                name=cmd.name,
            )
            await uow.holidays.add(holiday)
            await uow.commit()
            return holiday


@dataclass
class ListHolidaysUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: ListHolidaysCommand) -> Sequence[Holiday]:
        async with self.uow as uow:
            holidays = await uow.holidays.list_by_business(
                business_id=cmd.business_id, year=cmd.year, month=cmd.month
            )
            return sorted(holidays, key=lambda h: h.date)


@dataclass
class RenameHolidayUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: RenameHolidayCommand) -> Holiday:
        async with self.uow as uow:
            holiday = await uow.holidays.get_by_business_and_date(
                business_id=cmd.business_id, date_=cmd.date
            )
            if not holiday:
                raise HolidayNotFoundError(
                    business_id=str(cmd.business_id), date=str(cmd.date)
                )

            holiday.rename(cmd.new_name)

            await uow.holidays.update(holiday)
            await uow.commit()

            return holiday


@dataclass
class DeleteHolidayUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: DeleteHolidayCommand) -> None:
        async with self.uow as uow:
            await uow.holidays.delete_by_business_and_date(
                business_id=cmd.business_id, date_=cmd.date
            )
            await uow.commit()


@dataclass
class GetHolidayByDateUseCase:
    uow: UnitOfWorkPort

    async def execute(self, cmd: GetHolidayByDateCommand) -> Holiday | None:
        async with self.uow as uow:
            holiday = await uow.holidays.get_by_business_and_date(
                business_id=cmd.business_id, date_=cmd.date
            )
            return holiday
