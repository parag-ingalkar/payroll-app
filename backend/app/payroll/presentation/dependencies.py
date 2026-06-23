from __future__ import annotations

from fastapi import Depends

from app.core.db import get_session_factory
from app.payroll.application.use_cases import (
    GetPayrollRunUseCase,
    ListPayrollRunsUseCase,
    RunPayrollUseCase,
)
from app.payroll.domain.engine import PayrollCalculationEngine


def get_run_payroll_use_case(
    session_factory=Depends(get_session_factory),
) -> RunPayrollUseCase:
    return RunPayrollUseCase(
        uow_factory=session_factory,
        engine=PayrollCalculationEngine(),
    )


def get_get_payroll_run_use_case(
    session_factory=Depends(get_session_factory),
) -> GetPayrollRunUseCase:
    return GetPayrollRunUseCase(uow_factory=session_factory)


def get_list_payroll_runs_use_case(
    session_factory=Depends(get_session_factory),
) -> ListPayrollRunsUseCase:
    return ListPayrollRunsUseCase(uow_factory=session_factory)
