from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from app.business.domain.value_objects import normalize_whitespace
from app.holidays.domain.exceptions import InvalidHolidayNameError


@dataclass
class Holiday:
    id: UUID
    business_id: UUID
    date: date
    name: str | None

    @classmethod
    def create(cls, business_id: UUID, date_: date, name: str | None) -> "Holiday":
        if name:
            normalized_name = normalize_whitespace(name)
            if not normalized_name:
                raise InvalidHolidayNameError(
                    "Holiday name cannot be empty or whitespace."
                )
        else:
            normalized_name = None
        return cls(
            id=uuid4(),
            business_id=business_id,
            date=date_,
            name=normalized_name,
        )

    def rename(self, new_name: str):
        normalized_name = normalize_whitespace(new_name)
        if not normalized_name:
            raise InvalidHolidayNameError("Holiday name cannot be empty or whitespace.")
        if normalized_name == self.name:
            raise InvalidHolidayNameError(
                "New name must be different from the current name."
            )
        self.name = normalized_name
