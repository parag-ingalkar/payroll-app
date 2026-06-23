from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base  # project-wide declarative Base
from app.business.domain.value_objects import SalaryBasis, WageType
from app.payroll.domain.entities import (
    PayrollLineItem,
    PayrollRun,
    PayrollRunStatus,
)
from app.payroll.domain.value_objects import PayrollPeriod


class PayrollRunModel(Base):
    __tablename__ = "payroll_runs"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True)
    business_id: Mapped[UUID] = mapped_column(sa.Uuid, nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(sa.Date, nullable=False)
    period_end: Mapped[datetime] = mapped_column(sa.Date, nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    is_incomplete: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )

    line_items: Mapped[list["PayrollLineItemModel"]] = relationship(
        "PayrollLineItemModel",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @classmethod
    def from_entity(cls, run: PayrollRun) -> "PayrollRunModel":
        return cls(
            id=run.id,
            business_id=run.business_id,
            period_start=run.period.start_date,
            period_end=run.period.end_date,
            status=run.status.value,
            is_incomplete=run.is_incomplete,
            created_at=run.created_at,
            updated_at=run.updated_at,
            line_items=[PayrollLineItemModel.from_entity(li) for li in run.line_items],
        )

    def to_entity(self) -> PayrollRun:
        return PayrollRun(
            id=self.id,
            business_id=self.business_id,
            period=PayrollPeriod(
                start_date=self.period_start,
                end_date=self.period_end,
            ),
            status=PayrollRunStatus(self.status),
            is_incomplete=self.is_incomplete,
            created_at=self.created_at,
            updated_at=self.updated_at,
            line_items=[li.to_entity() for li in self.line_items],
        )


class PayrollLineItemModel(Base):
    __tablename__ = "payroll_line_items"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True)
    payroll_run_id: Mapped[UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("payroll_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[UUID] = mapped_column(sa.Uuid, nullable=False)
    employee_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)

    wage_type: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    wage_rate: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False)
    working_hours_per_day: Mapped[Decimal] = mapped_column(
        sa.Numeric(6, 2), nullable=False
    )
    overtime_multiplier: Mapped[Decimal] = mapped_column(
        sa.Numeric(6, 2), nullable=False
    )
    salary_basis: Mapped[str] = mapped_column(sa.String(30), nullable=False)

    basis_days: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    total_days_in_period: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    paid_days: Mapped[Decimal] = mapped_column(sa.Numeric(6, 2), nullable=False)
    lop_days: Mapped[Decimal] = mapped_column(sa.Numeric(6, 2), nullable=False)
    weekly_off_days: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    holiday_days: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    overtime_hours: Mapped[Decimal] = mapped_column(sa.Numeric(8, 2), nullable=False)

    per_day_rate: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False)
    per_hour_rate: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False)
    base_pay: Mapped[Decimal] = mapped_column(sa.Numeric(14, 2), nullable=False)
    overtime_pay: Mapped[Decimal] = mapped_column(sa.Numeric(14, 2), nullable=False)
    gross_pay: Mapped[Decimal] = mapped_column(sa.Numeric(14, 2), nullable=False)

    run: Mapped["PayrollRunModel"] = relationship(
        "PayrollRunModel", back_populates="line_items"
    )

    @classmethod
    def from_entity(cls, li: PayrollLineItem) -> "PayrollLineItemModel":
        return cls(
            id=li.id,
            payroll_run_id=li.payroll_run_id,
            employee_id=li.employee_id,
            employee_name=li.employee_name,
            wage_type=li.wage_type.value,
            wage_rate=li.wage_rate,
            working_hours_per_day=li.working_hours_per_day,
            overtime_multiplier=li.overtime_multiplier,
            salary_basis=li.salary_basis.value,
            basis_days=li.basis_days,
            total_days_in_period=li.total_days_in_period,
            paid_days=li.paid_days,
            lop_days=li.lop_days,
            weekly_off_days=li.weekly_off_days,
            holiday_days=li.holiday_days,
            overtime_hours=li.overtime_hours,
            per_day_rate=li.per_day_rate,
            per_hour_rate=li.per_hour_rate,
            base_pay=li.base_pay,
            overtime_pay=li.overtime_pay,
            gross_pay=li.gross_pay,
        )

    def to_entity(self) -> PayrollLineItem:
        return PayrollLineItem(
            id=self.id,
            payroll_run_id=self.payroll_run_id,
            employee_id=self.employee_id,
            employee_name=self.employee_name,
            wage_type=WageType(self.wage_type),
            wage_rate=self.wage_rate,
            working_hours_per_day=self.working_hours_per_day,
            overtime_multiplier=self.overtime_multiplier,
            salary_basis=SalaryBasis(self.salary_basis),
            basis_days=self.basis_days,
            total_days_in_period=self.total_days_in_period,
            paid_days=self.paid_days,
            lop_days=self.lop_days,
            weekly_off_days=self.weekly_off_days,
            holiday_days=self.holiday_days,
            overtime_hours=self.overtime_hours,
            per_day_rate=self.per_day_rate,
            per_hour_rate=self.per_hour_rate,
            base_pay=self.base_pay,
            overtime_pay=self.overtime_pay,
            gross_pay=self.gross_pay,
        )
