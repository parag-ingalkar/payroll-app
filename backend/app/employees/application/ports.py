from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.employees.domain.entities import Employee


class EmployeeRepositoryPort(Protocol):
    async def add(self, employee: Employee) -> None: ...

    async def get_by_business_and_id(
        self, business_id: UUID, employee_id: UUID
    ) -> Employee | None: ...

    async def list_by_business(
        self, business_id: UUID, is_active: bool | None = None
    ) -> Sequence[Employee]: ...

    async def update(self, employee: Employee) -> None: ...

    async def delete(self, employee: Employee) -> None: ...

    async def list_active_for_business(
        self, business_id: UUID
    ) -> Sequence[Employee]: ...

    async def list_by_ids(
        self, business_id: UUID, employee_ids: list[UUID]
    ) -> Sequence[Employee]: ...
