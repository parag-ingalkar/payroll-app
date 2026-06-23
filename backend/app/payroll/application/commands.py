from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class RunPayrollCommand:
    business_id: UUID
    owner_id: str
    year: int
    month: int
    employee_ids: list[UUID] | None = None  # None => all active employees


@dataclass
class GetPayrollRunCommand:
    business_id: UUID
    owner_id: str
    run_id: UUID


@dataclass
class ListPayrollRunsCommand:
    business_id: UUID
    owner_id: str
    year: int | None = None
    month: int | None = None
    employee_id: UUID | None = None
