from datetime import date
from uuid import UUID
from typing import Protocol
from collections.abc import Sequence

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
