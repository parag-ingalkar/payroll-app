import uuid
from decimal import Decimal

from app.employees.infrastructure.models import EmployeeModel
from app.holidays.infrastructure.models import HolidayModel
from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.shared.value_objects import Weekday, SalaryBasis, WageType
from app.businesses.domain.entities import Business, WeeklyOffRule


class BusinessModel(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)

    default_salary_basis: Mapped[SalaryBasis] = mapped_column(
        Enum(SalaryBasis, name="salary_basis_enum"),
        nullable=False,
    )
    payroll_start_day: Mapped[int] = mapped_column(Integer, nullable=False)
    default_wage_type: Mapped[WageType] = mapped_column(
        Enum(WageType, name="wage_type_enum"), nullable=False
    )
    default_working_hours_per_day: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False
    )
    default_overtime_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), nullable=False
    )

    weekly_off_rules: Mapped[list["WeeklyOffRuleModel"]] = relationship(
        "WeeklyOffRuleModel",
        back_populates="business",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    holidays: Mapped[list["HolidayModel"]] = relationship(
        "HolidayModel",
        back_populates="business",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    employees: Mapped[list["EmployeeModel"]] = relationship(
        "EmployeeModel",
        back_populates="business",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("owner_id", "slug", name="uq_business_owner_slug"),
        CheckConstraint(
            "default_working_hours_per_day > 0 AND default_working_hours_per_day <= 24",
            name="check_default_working_hours_per_day",
        ),
        CheckConstraint(
            "default_overtime_multiplier >= 1", name="check_default_overtime_multiplier"
        ),
        CheckConstraint(
            "payroll_start_day >= 1 AND payroll_start_day <= 28",
            name="check_payroll_start_day",
        ),
    )

    @classmethod
    def from_entity(cls, business: "Business") -> "BusinessModel":

        weekly_off_rules = [
            WeeklyOffRuleModel.from_entity(rule) for rule in business.weekly_off_rules
        ]
        return cls(
            id=business.id,
            owner_id=business.owner_id,
            name=business.name,
            slug=business.slug,
            default_salary_basis=business.default_salary_basis,
            payroll_start_day=business.payroll_start_day,
            default_wage_type=business.default_wage_type,
            default_working_hours_per_day=business.default_working_hours_per_day,
            default_overtime_multiplier=business.default_overtime_multiplier,
            weekly_off_rules=weekly_off_rules,
        )

    def to_entity(self) -> "Business":
        return Business(
            id=self.id,
            owner_id=self.owner_id,
            name=self.name,
            slug=self.slug,
            default_salary_basis=self.default_salary_basis,
            payroll_start_day=self.payroll_start_day,
            default_wage_type=self.default_wage_type,
            default_working_hours_per_day=self.default_working_hours_per_day,
            default_overtime_multiplier=self.default_overtime_multiplier,
            weekly_off_rules=[rule.to_entity() for rule in self.weekly_off_rules],
        )


class WeeklyOffRuleModel(Base):
    __tablename__ = "weekly_off_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    weekday: Mapped[Weekday] = mapped_column(
        Enum(Weekday, name="weekday_enum"), nullable=False
    )

    business: Mapped[BusinessModel] = relationship(
        back_populates="weekly_off_rules",
    )

    __table_args__ = (
        UniqueConstraint(
            "business_id", "weekday", name="uq_weekly_off_rule_business_weekday"
        ),
        Index("ix_weekly_off_rule_business_id", "business_id"),
    )

    @classmethod
    def from_entity(cls, rule: "WeeklyOffRule") -> "WeeklyOffRuleModel":
        return cls(
            id=rule.id,
            weekday=rule.weekday,
        )

    def to_entity(self) -> "WeeklyOffRule":
        return WeeklyOffRule(
            id=self.id,
            weekday=self.weekday,
        )
