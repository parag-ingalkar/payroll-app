from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from app.business.domain.exceptions import InvalidWeeklyOffRulesError
from app.business.domain.value_objects import (
    SalaryBasis,
    WageType,
    Weekday,
    normalize_whitespace,
)


@dataclass
class WeeklyOffRule:
    weekday: Weekday
    # None means "every week"; otherwise 1-5 for week-of-month
    week_of_month: int | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass
class Business:
    owner_id: str
    name: str
    default_wage_type: WageType
    default_working_hours_per_day: Decimal
    default_overtime_multiplier: Decimal
    default_salary_basis: SalaryBasis
    payroll_start_day: int = 1
    weekly_off_rules: list[WeeklyOffRule] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self):
        self._validate_default_working_hours_per_day()
        self._validate_default_overtime_multiplier()
        self._validate_payroll_start_day()
        self._validate_weekly_off_rules()

    def _validate_default_working_hours_per_day(self) -> None:
        if (
            self.default_working_hours_per_day <= 0
            or self.default_working_hours_per_day > Decimal("24")
        ):
            raise ValueError(
                "Default working hours per day must be greater than 0 and at most 24."
            )

    def _validate_default_overtime_multiplier(self) -> None:
        if self.default_overtime_multiplier < 1:
            raise ValueError("Default overtime multiplier must be at least 1.")

    def _validate_payroll_start_day(self) -> None:
        if not (1 <= self.payroll_start_day <= 28):
            raise ValueError("Payroll start day must be between 1 and 28.")

    def _validate_weekly_off_rules(self) -> None:
        by_weekday: dict[Weekday, list[WeeklyOffRule]] = defaultdict(list)
        for rule in self.weekly_off_rules:
            by_weekday[rule.weekday].append(rule)

        for weekday, rules in by_weekday.items():
            seen_pairs: set[tuple[Weekday, int | None]] = set()
            has_every_week = any(r.week_of_month is None for r in rules)
            has_specific_weeks = any(r.week_of_month is not None for r in rules)

            # No duplicates
            for r in rules:
                key = (r.weekday, r.week_of_month)
                if key in seen_pairs:
                    raise InvalidWeeklyOffRulesError(
                        f"Duplicate weekly off rule for {weekday} and {r.week_of_month}."
                    )
                seen_pairs.add(key)

            # No every-week + specific-week combo
            if has_every_week and has_specific_weeks:
                raise InvalidWeeklyOffRulesError(
                    f"Weekday {weekday} cannot have both every-week and specific-week rules."
                )

    def is_weekly_off(self, d: date) -> bool:
        """Return True if the given date falls on a weekly off day for this business."""
        date_weekday_name = d.strftime("%A").lower()  # e.g. "monday"
        try:
            date_weekday = Weekday(date_weekday_name)
        except ValueError:
            return False
        week_of_month = (d.day - 1) // 7 + 1
        for rule in self.weekly_off_rules:
            if rule.weekday != date_weekday:
                continue
            if rule.week_of_month is None or rule.week_of_month == week_of_month:
                return True
        return False

    def replace_weekly_off_rules(self, rules: list[WeeklyOffRule]) -> None:
        self.weekly_off_rules = rules
        self._validate_weekly_off_rules()

    def rename(self, new_name: str) -> None:
        normalized_name = normalize_whitespace(new_name)
        if not normalized_name:
            raise ValueError("Business name cannot be empty or whitespace.")
        self.name = normalized_name

    def update_defaults(
        self,
        *,
        default_wage_type: WageType | None = None,
        default_working_hours_per_day: Decimal | None = None,
        default_overtime_multiplier: Decimal | None = None,
        default_salary_basis: SalaryBasis | None = None,
        payroll_start_day: int | None = None,
    ) -> None:
        if default_wage_type is not None:
            self.default_wage_type = default_wage_type
        if default_working_hours_per_day is not None:
            self.default_working_hours_per_day = default_working_hours_per_day
            self._validate_default_working_hours_per_day()
        if default_overtime_multiplier is not None:
            self.default_overtime_multiplier = default_overtime_multiplier
            self._validate_default_overtime_multiplier()
        if payroll_start_day is not None:
            self.payroll_start_day = payroll_start_day
            self._validate_payroll_start_day()
        if default_salary_basis is not None:
            self.default_salary_basis = default_salary_basis

    @classmethod
    def create(
        cls,
        owner_id: str,
        name: str,
        default_wage_type: WageType,
        default_working_hours_per_day: Decimal,
        default_overtime_multiplier: Decimal,
        default_salary_basis: SalaryBasis,
        payroll_start_day: int,
        weekly_off_rules: list[WeeklyOffRule],
    ) -> "Business":
        normalized_name = normalize_whitespace(name)
        if not normalized_name:
            raise ValueError("Business name cannot be empty or whitespace.")

        return cls(
            owner_id=owner_id,
            name=normalized_name,
            default_wage_type=default_wage_type,
            default_working_hours_per_day=default_working_hours_per_day,
            default_overtime_multiplier=default_overtime_multiplier,
            default_salary_basis=default_salary_basis,
            payroll_start_day=payroll_start_day,
            weekly_off_rules=weekly_off_rules,
        )
