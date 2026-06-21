from dataclasses import dataclass
from uuid import UUID
from datetime import date


@dataclass(slots=True)
class CreateHolidayCommand:
    business_id: UUID
    owner_id: str
    date: date
    name: str | None = None


@dataclass(slots=True)
class RenameHolidayCommand:
    business_id: UUID
    owner_id: str
    date: date
    new_name: str | None


@dataclass(slots=True)
class DeleteHolidayCommand:
    business_id: UUID
    owner_id: str
    date: date


@dataclass(slots=True)
class ListHolidaysCommand:
    business_id: UUID
    owner_id: str
    year: int | None = None
    month: int | None = None


@dataclass(slots=True)
class GetHolidayByDateCommand:
    business_id: UUID
    owner_id: str
    date: date


@dataclass(slots=True)
class IsHolidayCommand:
    business_id: UUID
    owner_id: str
    date: date


@dataclass(slots=True)
class GetHolidayByIDCommand:
    business_id: UUID
    owner_id: str
    holiday_id: UUID
