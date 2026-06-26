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
    GetHolidayCommand,
    ListHolidaysCommand,
    UpdateHolidayCommand,
)
from app.businesses.domain.exceptions import BusinessNotFoundError


@dataclass
class CreateHolidayUseCase:
    uow: UnitOfWorkPort

    async def execute(self, command: CreateHolidayCommand) -> Holiday:
        async with self.uow as uow:
            # Business ownership validation
            business = await uow.businesses.get_by_id_and_owner(
                command.business_id, command.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID {command.business_id} not found for owner {command.owner_id}."
                )
            
            # Check if the holiday already exists
            existing_holiday = await uow.holidays.get_by_business_and_date(
                command.business_id, command.holiday_date
            )
            if existing_holiday:
                raise HolidayAlreadyExistsError(
                    f"Holiday already exists for business_id={command.business_id} on date={command.holiday_date}."
                )
            
            # Create and add the new holiday
            new_holiday = Holiday.create(
                business_id=command.business_id,
                holiday_date=command.holiday_date,
                holiday_name=command.holiday_name,
                is_paid=command.is_paid,
            )
            await uow.holidays.add(new_holiday)
            await uow.commit()
            return new_holiday
        

@dataclass
class UpdateHolidayUseCase:
    uow: UnitOfWorkPort

    async def execute(self, command: UpdateHolidayCommand) -> Holiday:
        async with self.uow as uow:
            # Business ownership validation
            business = await uow.businesses.get_by_id_and_owner(
                command.business_id, command.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID {command.business_id} not found for owner {command.owner_id}."
                )
            
            # Retrieve the holiday to update
            holiday = await uow.holidays.get_by_business_and_date(
                command.business_id, command.holiday_date
            )
            if not holiday:
                raise HolidayNotFoundError(
                    f"Holiday not found for business_id={command.business_id} on date={command.holiday_date}."
                )
            
            # Update the holiday
            if command.new_name is not None:
                holiday.rename(command.new_name)
            if command.is_paid is not None:
                holiday.update_is_paid(command.is_paid)
                
            await uow.holidays.update(holiday)
            await uow.commit()
            return holiday
        

@dataclass
class DeleteHolidayUseCase:
    uow: UnitOfWorkPort

    async def execute(self, command: DeleteHolidayCommand) -> None:
        async with self.uow as uow:
            # Business ownership validation
            business = await uow.businesses.get_by_id_and_owner(
                command.business_id, command.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID {command.business_id} not found for owner {command.owner_id}."
                )
            
            # Retrieve the holiday to delete
            holiday = await uow.holidays.get_by_business_and_date(
                command.business_id, command.holiday_date
            )
            if not holiday:
                raise HolidayNotFoundError(
                    f"Holiday not found for business_id={command.business_id} on date={command.holiday_date}."
                )
            
            # Delete the holiday
            await uow.holidays.delete_by_business(command.business_id, command.holiday_date)
            await uow.commit()


@dataclass
class ListHolidaysUseCase:
    uow: UnitOfWorkPort

    async def execute(self, command: ListHolidaysCommand) -> Sequence[Holiday]:
        async with self.uow as uow:
            # Business ownership validation
            business = await uow.businesses.get_by_id_and_owner(
                command.business_id, command.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID {command.business_id} not found for owner {command.owner_id}."
                )
            
            # List holidays for the business
            holidays = await uow.holidays.list_by_business(
                command.business_id, command.year, command.month
            )
            return holidays
        
@dataclass
class GetHolidayUseCase:
    uow: UnitOfWorkPort

    async def execute(self, command: GetHolidayCommand) -> Holiday:
        async with self.uow as uow:
            # Business ownership validation
            business = await uow.businesses.get_by_id_and_owner(
                command.business_id, command.owner_id
            )
            if not business:
                raise BusinessNotFoundError(
                    f"Business with ID {command.business_id} not found for owner {command.owner_id}."
                )
            
            # Retrieve the holiday
            holiday = await uow.holidays.get_by_business_and_date(
                command.business_id, command.holiday_date
            )
            if not holiday:
                raise HolidayNotFoundError(
                    f"Holiday not found for business_id={command.business_id} on date={command.holiday_date}."
                )
            
            return holiday