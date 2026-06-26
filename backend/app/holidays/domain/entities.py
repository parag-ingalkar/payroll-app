from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from app.holidays.domain.exceptions import HolidayUpdateError, InvalidHolidayNameError


@dataclass
class Holiday:
    business_id: UUID
    holiday_date: date
    holiday_name: str | None
    is_paid: bool = True
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def create(
        cls,
        business_id: UUID,
        holiday_date: date,
        holiday_name: str | None,
        is_paid: bool = True,
    ) -> "Holiday":
        return cls(
            business_id=business_id,
            holiday_date=holiday_date,
            holiday_name=holiday_name,
            is_paid=is_paid,
        )

    def rename(self, new_name: str | None) -> None:

        if new_name == self.holiday_name:
            raise InvalidHolidayNameError(
                "New name must be different from the current name."
            )
        self.holiday_name = new_name or None

    def update_is_paid(self, is_paid: bool) -> None:
        if is_paid == self.is_paid:
            raise HolidayUpdateError(
                "New is_paid value must be different from the current value."
            )
        self.is_paid = is_paid
