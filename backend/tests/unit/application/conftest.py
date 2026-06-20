# tests/application_conftest.py
from collections.abc import Sequence
from uuid import UUID, uuid4

import pytest

from app.business.domain.entities import Business
from app.business.domain.value_objects import normalize_business_name_for_lookup
from app.business.application.ports import (
    BusinessRepositoryPort,
)
from app.core.uow import UnitOfWorkPort


class InMemoryBusinessRepository(BusinessRepositoryPort):
    def __init__(self, items: list[Business] | None = None) -> None:
        self._items: list[Business] = list(items or [])

    async def add(self, business: Business) -> None:
        if business.id is None:
            business.id = uuid4()
        self._items.append(business)

    async def get_by_id_and_owner(
        self, business_id: UUID, owner_id: str
    ) -> Business | None:
        return next(
            (b for b in self._items if b.id == business_id and b.owner_id == owner_id),
            None,
        )

    async def list_by_owner(self, owner_id: str) -> Sequence[Business]:
        return [b for b in self._items if b.owner_id == owner_id]

    async def find_by_normalized_name(
        self, owner_id: str, normalized_name: str
    ) -> Business | None:
        for b in self._items:
            if b.owner_id != owner_id:
                continue
            if normalize_business_name_for_lookup(b.name) == normalized_name:
                return b
        return None

    async def find_by_owner_and_name(self, owner_id: str, name: str) -> Business | None:
        normalized_name = normalize_business_name_for_lookup(name)
        for b in self._items:
            if b.owner_id != owner_id:
                continue
            if normalize_business_name_for_lookup(b.name) == normalized_name:
                return b
        return None

    async def delete(self, business: Business) -> None:
        self._items = [b for b in self._items if b is not business]

    async def update(self, business: Business) -> None:
        for idx, b in enumerate(self._items):
            if b.id == business.id:
                self._items[idx] = business
                return


class InMemoryUnitOfWork(UnitOfWorkPort):
    def __init__(self, repo: InMemoryBusinessRepository) -> None:
        self.businesses = repo
        self.committed = False

    async def __aenter__(self) -> "InMemoryUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.committed = False


@pytest.fixture
def in_memory_business_repo(business_defaults) -> InMemoryBusinessRepository:
    business = Business.create(**business_defaults)
    return InMemoryBusinessRepository(items=[business])


@pytest.fixture
def in_memory_uow(
    in_memory_business_repo: InMemoryBusinessRepository,
) -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork(in_memory_business_repo)
