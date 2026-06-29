from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from uuid import UUID

from app.businesses.domain.entities import WeeklyOffRule


class PayrollStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"

class AdjustmentType(StrEnum):
    BONUS = "bonus"
    DEDUCTION = "deduction"


@dataclass(slots=True, frozen=True)
class PayrollPeriod:
    year: int
    month: int

    start_date: date
    end_date: date

    def contains(self, check_date: date) -> bool:
        return self.start_date <= check_date <= self.end_date
    


@dataclass
class MissingAttendanceWarning:
    employee_id: UUID
    missing_dates: Sequence[date]