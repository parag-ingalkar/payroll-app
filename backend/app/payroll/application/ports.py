from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.payroll.domain.entities import PayrollRun
from app.payroll.domain.value_objects import PayrollPeriod


class PayrollRepositoryPort(Protocol):
    async def add(self, run: PayrollRun) -> None: ...

    async def get(self, business_id: UUID, run_id: UUID) -> PayrollRun | None: ...

    async def list(
        self,
        business_id: UUID,
        period: PayrollPeriod | None = None,
        employee_id: UUID | None = None,
    ) -> list[PayrollRun]: ...

    async def delete_for_period(
        self,
        business_id: UUID,
        period: PayrollPeriod,
    ) -> None: ...
