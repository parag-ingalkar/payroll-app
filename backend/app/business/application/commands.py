from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.business.domain.entities import WageType, Weekday


@dataclass(slots=True)
class WeeklyOffRuleInput:
    weekday: Weekday
    week_of_month: int | None


@dataclass(slots=True)
class CreateBusinessCommand:
    owner_id: str
    name: str
    default_wage_type: WageType
    default_working_hours_per_day: Decimal
    default_overtime_multiplier: Decimal
    payroll_start_day: int
    weekly_off_rules: list[WeeklyOffRuleInput]


@dataclass(slots=True)
class UpdateBusinessCommand:
    business_id: UUID
    owner_id: str
    name: str | None = None
    default_wage_type: WageType | None = None
    default_working_hours_per_day: Decimal | None = None
    default_overtime_multiplier: Decimal | None = None
    payroll_start_day: int | None = None


@dataclass(slots=True)
class ReplaceWeeklyOffRulesCommand:
    business_id: UUID
    owner_id: str
    weekly_off_rules: list[WeeklyOffRuleInput]