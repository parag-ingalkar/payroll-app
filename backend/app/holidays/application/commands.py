from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(slots=True)
class CreateHolidayCommand:
    business_id: UUID
    owner_id: str
    holiday_date: date
    holiday_name: str | None
    is_paid: bool = True

@dataclass(slots=True)
class UpdateHolidayCommand:
    business_id: UUID
    owner_id: str
    holiday_date: date
    new_name: str | None = None
    is_paid: bool | None = None

@dataclass(slots=True)
class DeleteHolidayCommand:
    business_id: UUID
    owner_id: str
    holiday_date: date

@dataclass(slots=True)
class ListHolidaysCommand:
    business_id: UUID
    owner_id: str
    year: int | None = None
    month: int | None = None

@dataclass(slots=True)
class GetHolidayCommand:
    business_id: UUID
    owner_id: str
    holiday_date: date