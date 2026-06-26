from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.employees.application.ports import EmployeeRepositoryPort
from app.employees.domain.entities import Employee
from app.employees.infrastructure.models import EmployeeModel


class SqlEmployeeRepository(EmployeeRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, employee: Employee) -> None:
        model = EmployeeModel.from_entity(employee)
        self.session.add(model)
        await self.session.flush()

    async def get_by_business_and_id(
        self, business_id: UUID, employee_id: UUID
    ) -> Employee | None:
        result = await self.session.execute(
            select(EmployeeModel).where(
                EmployeeModel.business_id == business_id,
                EmployeeModel.id == employee_id,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list_by_business(
        self, business_id: UUID, is_active: bool | None = None
    ) -> Sequence[Employee]:
        stmt = select(EmployeeModel).where(EmployeeModel.business_id == business_id)
        if is_active is not None:
            stmt = stmt.where(EmployeeModel.is_active == is_active)
        result = await self.session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def update(self, employee: Employee) -> None:
        result = await self.session.execute(
            select(EmployeeModel).where(
                EmployeeModel.business_id == employee.business_id,
                EmployeeModel.id == employee.id,
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return
        model.name = employee.name
        model.designation = employee.designation
        model.wage_type = employee.wage_type
        model.wage_rate = employee.wage_rate
        model.working_hours_per_day = employee.working_hours_per_day
        model.overtime_multiplier = employee.overtime_multiplier
        model.is_active = employee.is_active
        await self.session.flush()

    async def delete(self, employee: Employee) -> None:
        result = await self.session.execute(
            select(EmployeeModel).where(
                EmployeeModel.business_id == employee.business_id,
                EmployeeModel.id == employee.id,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)

    async def list_active_for_business(self, business_id: UUID) -> Sequence[Employee]:
        return await self.list_by_business(business_id, is_active=True)

    async def list_by_ids(
        self, business_id: UUID, employee_ids: list[UUID]
    ) -> Sequence[Employee]:
        result = await self.session.execute(
            select(EmployeeModel).where(
                EmployeeModel.business_id == business_id,
                EmployeeModel.id.in_(employee_ids),
            )
        )
        return [m.to_entity() for m in result.scalars().all()]