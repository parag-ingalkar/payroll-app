from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.businesses.domain.entities import Business, WeeklyOffRule
from app.businesses.domain.value_objects import BusinessPayrollConfiguration


class BusinessRepositoryPort(Protocol):
    async def add(self, business: Business) -> None: ...

    async def get_by_id_and_owner(
        self, business_id: UUID, owner_id: str
    ) -> Business | None: ...

    async def get_by_owner_and_slug(
        self, owner_id: str, slug: str
    ) -> Business | None: ...

    async def list_by_owner(self, owner_id: str) -> Sequence[Business]: ...

    async def update(self, business: Business) -> None: ...

    async def delete(self, business: Business) -> None: ...

    # async def get_weekly_off_rules(self, business_id: UUID, owner_id: str) -> Sequence[WeeklyOffRule]:
    #     ...

    async def replace_weekly_off_rules(
        self, business_id: UUID, new_rules: Sequence[WeeklyOffRule]
    ) -> None: ...

    async def get_business_payroll_configuration(
        self,
        *,
        business_id: UUID,
    ) -> BusinessPayrollConfiguration: ...
