from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.payroll.domain.entities import PayrollRun
from app.payroll.domain.value_objects import PayrollPeriod

from .orm import PayrollRunModel


class SqlAlchemyPayrollRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, run: PayrollRun) -> None:
        model = PayrollRunModel.from_entity(run)
        self.session.add(model)

    async def get(self, business_id: UUID, run_id: UUID) -> PayrollRun | None:
        result = await self.session.execute(
            sa.select(PayrollRunModel).where(
                PayrollRunModel.id == run_id,
                PayrollRunModel.business_id == business_id,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list(
        self,
        business_id: UUID,
        period: PayrollPeriod | None = None,
        employee_id: UUID | None = None,
    ) -> list[PayrollRun]:
        stmt = sa.select(PayrollRunModel).where(
            PayrollRunModel.business_id == business_id
        )

        if period is not None:
            stmt = stmt.where(
                PayrollRunModel.period_start == period.start_date,
                PayrollRunModel.period_end == period.end_date,
            )

        if employee_id is not None:
            from .orm import PayrollLineItemModel

            stmt = (
                stmt.join(
                    PayrollLineItemModel,
                    PayrollLineItemModel.payroll_run_id == PayrollRunModel.id,
                )
                .where(PayrollLineItemModel.employee_id == employee_id)
                .distinct()
            )

        result = await self.session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def delete_for_period(
        self,
        business_id: UUID,
        period: PayrollPeriod,
    ) -> None:
        await self.session.execute(
            sa.delete(PayrollRunModel).where(
                PayrollRunModel.business_id == business_id,
                PayrollRunModel.period_start == period.start_date,
                PayrollRunModel.period_end == period.end_date,
            )
        )
