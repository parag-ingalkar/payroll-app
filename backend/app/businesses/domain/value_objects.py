from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from app.businesses.domain.entities import WeeklyOffRule


@dataclass(slots=True, frozen=True)
class BusinessPayrollConfiguration:
    business_id: UUID
    payroll_start_day: int
    weekly_off_rules: Sequence[WeeklyOffRule]