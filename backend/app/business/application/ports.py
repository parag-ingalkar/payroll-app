from collections.abc import Sequence
from uuid import UUID
from typing import Protocol

from app.business.domain.entities import Business


class BusinessRepositoryPort(Protocol):
    async def add(self, business: Business) -> None: ...

    async def get_by_id_and_owner(
        self, business_id: UUID, owner_id: str
    ) -> Business | None: ...

    async def list_by_owner(self, owner_id: str) -> Sequence[Business]: ...

    async def find_by_normalized_name(
        self, owner_id: str, normalized_name: str
    ) -> Business | None: ...

    async def find_by_owner_and_name(
        self, owner_id: str, name: str
    ) -> Business | None: ...

    async def delete(self, business: Business) -> None: ...

    async def update(self, business: Business) -> None: ...

