from __future__ import annotations
from typing import TYPE_CHECKING
from decimal import Decimal
from uuid import uuid4, UUID

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.business.domain.entities import WageType, Weekday

if TYPE_CHECKING:
    from app.holidays.infrastructure.orm import HolidayModel


class BusinessModel(Base):
    __tablename__ = "businesses"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    owner_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    # display name (already whitespace-normalized)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # normalized for uniqueness (lowercased, whitespace-collapsed)
    normalized_name: Mapped[str] = mapped_column(String(100), nullable=False)

    default_wage_type: Mapped[WageType] = mapped_column(
        Enum(WageType, name="wage_type", native_enum=False),
        nullable=False,
    )
    default_working_hours_per_day: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    default_overtime_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    payroll_start_day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
    )

    weekly_off_rules: Mapped[list["BusinessWeeklyOffRuleModel"]] = relationship(
        back_populates="business",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    holidays: Mapped[list["HolidayModel"]] = relationship(
        back_populates="business",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "owner_id",
            "normalized_name",
            name="uq_business_owner_normalized_name",
        ),
        CheckConstraint(
            "payroll_start_day >= 1 AND payroll_start_day <= 28",
            name="ck_business_payroll_start_day",
        ),
    )


class BusinessWeeklyOffRuleModel(Base):
    __tablename__ = "business_weekly_off_rules"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    business_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weekday: Mapped[Weekday] = mapped_column(
        Enum(Weekday, name="weekday", native_enum=False),
        nullable=False,
    )
    week_of_month: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    business: Mapped[BusinessModel] = relationship(
        back_populates="weekly_off_rules",
    )

    __table_args__ = (
        CheckConstraint(
            "week_of_month IS NULL OR (week_of_month >= 1 AND week_of_month <= 5)",
            name="ck_weekly_off_rule_week_of_month",
        ),
    )
