from collections.abc import Sequence
from datetime import date
from typing import Protocol
from uuid import UUID

from app.holidays.domain.entities import Holiday


class HolidayRepositoryPort(Protocol):
    async def add(self, holiday: Holiday) -> None: ...

    async def get_by_business_and_date(
        self, business_id: UUID, date_: date
    ) -> Holiday | None: ...

    async def get_by_business_and_id(
        self, business_id: UUID, holiday_id: UUID
    ) -> Holiday | None: ...

    async def list_by_business(
        self, business_id: UUID, year: int | None = None, month: int | None = None
    ) -> Sequence[Holiday]: ...

    async def delete_by_business_and_date(
        self, business_id: UUID, date_: date
    ) -> None: ...

    async def update(self, holiday: Holiday) -> None: ...

    async def list_for_period(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Sequence[Holiday]: ...
