from collections.abc import Sequence
from datetime import date
from typing import Protocol
from uuid import UUID

from app.holidays.domain.entities import Holiday


class HolidaysRepositoryPort(Protocol):
    """Protocol for the holidays repository."""

    async def add(self, holiday: Holiday) -> None:
        """Add a new holiday to the repository."""
        ...

    async def get_by_business_and_date(
        self, business_id: UUID, holiday_date: date
    ) -> Holiday | None:
        """Retrieve a holiday by business ID and date."""
        ...

    async def list_by_business(
        self, business_id: UUID, year: int | None = None, month: int | None = None
    ) -> Sequence[Holiday]:
        """List holidays for a business, optionally filtered by year and month."""
        ...

    async def delete_by_business(self, business_id: UUID, holiday_date: date) -> None:
        """Delete a holiday by business ID and date."""
        ...

    async def update(self, holiday: Holiday) -> None: ...

    async def list_for_period(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Sequence[Holiday]: ...
