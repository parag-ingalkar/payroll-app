from dataclasses import dataclass
from uuid import UUID
from datetime import date


@dataclass(slots=True)
class CreateHolidayCommand:
    business_id: UUID
    date: date
    name: str | None = None


@dataclass(slots=True)
class RenameHolidayCommand:
    business_id: UUID
    date: date
    new_name: str


@dataclass(slots=True)
class DeleteHolidayCommand:
    business_id: UUID
    date: date


@dataclass(slots=True)
class ListHolidaysCommand:
    business_id: UUID
    year: int | None = None
    month: int | None = None


@dataclass(slots=True)
class GetHolidayByDateCommand:
    business_id: UUID
    date: date


@dataclass(slots=True)
class IsHolidayCommand:
    business_id: UUID
    date: date


@dataclass(slots=True)
class GetHolidayByIDCommand:
    business_id: UUID
    holiday_id: UUID
