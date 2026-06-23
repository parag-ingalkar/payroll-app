from __future__ import annotations

from fastapi import Depends

from app.core.dependencies import get_uow
from app.core.uow import SqlAlchemyUnitOfWork
from app.payroll.application.use_cases import (
    GetPayrollRunUseCase,
    ListPayrollRunsUseCase,
    RunPayrollUseCase,
)
from app.payroll.domain.engine import PayrollCalculationEngine


def get_payroll_calculation_engine() -> PayrollCalculationEngine:
    return PayrollCalculationEngine()


def get_run_payroll_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    engine: PayrollCalculationEngine = Depends(get_payroll_calculation_engine),
) -> RunPayrollUseCase:
    return RunPayrollUseCase(uow, engine)


def get_get_payroll_run_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GetPayrollRunUseCase:
    return GetPayrollRunUseCase(uow)


def get_list_payroll_runs_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ListPayrollRunsUseCase:
    return ListPayrollRunsUseCase(uow)
