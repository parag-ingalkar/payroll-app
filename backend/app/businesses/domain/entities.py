from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date
from uuid import UUID, uuid4

from app.shared.value_objects import Weekday, SalaryBasis, WageType
from app.businesses.domain.exceptions import InvalidWeeklyOffRulesError


@dataclass
class WeeklyOffRule:
    weekday: Weekday
    id: UUID = field(default_factory=uuid4)


@dataclass
class Business:
    owner_id: str
    name: str
    slug: str

    default_salary_basis: SalaryBasis
    payroll_start_day: int
    default_wage_type: WageType
    default_working_hours_per_day: Decimal
    default_overtime_multiplier: Decimal

    weekly_off_rules: Sequence[WeeklyOffRule]

    id: UUID = field(default_factory=uuid4)

    def __post_init__(self):
        self._validate_default_working_hours_per_day()
        self._validate_default_overtime_multiplier()
        self._validate_payroll_start_day()
        self._validate_weekly_off_rules()
        self.slug = self._generate_slug()

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
        weekdays = [rule.weekday for rule in self.weekly_off_rules]
        if len(weekdays) != len(set(weekdays)):
            raise InvalidWeeklyOffRulesError(
                "Duplicate weekdays found in weekly off rules."
            )

    def _generate_slug(self) -> str:
        # Generate a slug from the business name
        # Trim whitespace, convert to lowercase, and replace spaces with hyphens
        slug = self.name.strip().lower().replace(" ", "-")
        return slug

    def update(
        self,
        *,
        new_name: str | None = None,
        default_wage_type: WageType | None = None,
        default_working_hours_per_day: Decimal | None = None,
        default_overtime_multiplier: Decimal | None = None,
        default_salary_basis: SalaryBasis | None = None,
        payroll_start_day: int | None = None,
    ) -> None:
        if new_name:
            self.name = new_name
            self.slug = self._generate_slug()
        if default_wage_type:
            self.default_wage_type = default_wage_type
        if default_working_hours_per_day:
            self.default_working_hours_per_day = default_working_hours_per_day
            self._validate_default_working_hours_per_day()
        if default_overtime_multiplier:
            self.default_overtime_multiplier = default_overtime_multiplier
            self._validate_default_overtime_multiplier()
        if payroll_start_day:
            self.payroll_start_day = payroll_start_day
            self._validate_payroll_start_day()
        if default_salary_basis:
            self.default_salary_basis = default_salary_basis

    def replace_weekly_off_rules(self, rules: Sequence[WeeklyOffRule]) -> None:
        self.weekly_off_rules = rules
        self._validate_weekly_off_rules()

    def is_weekly_off(self, date: date) -> bool:
        # Get the abbreviated weekday name and convert to lowercase
        weekday = date.strftime("%a").lower()
        return any(rule.weekday == weekday for rule in self.weekly_off_rules)

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        name: str,
        default_salary_basis: SalaryBasis,
        payroll_start_day: int,
        default_wage_type: WageType,
        default_working_hours_per_day: Decimal,
        default_overtime_multiplier: Decimal,
        weekly_off_rules: Sequence[WeeklyOffRule],
    ) -> "Business":
        return cls(
            owner_id=owner_id,
            name=name,
            slug="",  # Slug will be generated in __post_init__
            default_salary_basis=default_salary_basis,
            payroll_start_day=payroll_start_day,
            default_wage_type=default_wage_type,
            default_working_hours_per_day=default_working_hours_per_day,
            default_overtime_multiplier=default_overtime_multiplier,
            weekly_off_rules=weekly_off_rules,
        )
