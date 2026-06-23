from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentPrincipal, get_current_user
from app.payroll.application.commands import (
    GetPayrollRunCommand,
    ListPayrollRunsCommand,
    RunPayrollCommand,
)
from app.payroll.application.use_cases import (
    GetPayrollRunUseCase,
    ListPayrollRunsUseCase,
    RunPayrollUseCase,
)

from .dependencies import (
    get_get_payroll_run_use_case,
    get_list_payroll_runs_use_case,
    get_run_payroll_use_case,
)
from .schemas import (
    PayrollLineItemRead,
    PayrollPeriodRead,
    PayrollRunRead,
    PayrollRunSummary,
    RunPayrollRequest,
)

router = APIRouter()


@router.post(
    "/run",
    response_model=PayrollRunRead,
    status_code=status.HTTP_200_OK,
    summary="Run (or re-run) payroll for a period",
)
async def run_payroll(
    business_id: UUID,
    payload: RunPayrollRequest,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: RunPayrollUseCase = Depends(get_run_payroll_use_case),
) -> PayrollRunRead:
    cmd = RunPayrollCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        year=payload.year,
        month=payload.month,
        employee_ids=payload.employee_ids,
    )
    run = await use_case.execute(cmd)

    return PayrollRunRead(
        id=run.id,
        business_id=run.business_id,
        period=PayrollPeriodRead(
            start_date=run.period.start_date,
            end_date=run.period.end_date,
        ),
        status=run.status,
        is_incomplete=run.is_incomplete,
        created_at=run.created_at,
        updated_at=run.updated_at,
        line_items=[PayrollLineItemRead.model_validate(li) for li in run.line_items],
    )


@router.get(
    "/",
    response_model=list[PayrollRunSummary],
    summary="List payroll runs for a business",
)
async def list_payroll_runs(
    business_id: UUID,
    year: int | None = None,
    month: int | None = None,
    employee_id: UUID | None = None,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ListPayrollRunsUseCase = Depends(get_list_payroll_runs_use_case),
) -> list[PayrollRunSummary]:
    cmd = ListPayrollRunsCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        year=year,
        month=month,
        employee_id=employee_id,
    )
    runs = await use_case.execute(cmd)

    summaries = []
    for run in runs:
        summaries.append(
            PayrollRunSummary(
                id=run.id,
                business_id=run.business_id,
                period=PayrollPeriodRead(
                    start_date=run.period.start_date,
                    end_date=run.period.end_date,
                ),
                status=run.status,
                is_incomplete=run.is_incomplete,
                created_at=run.created_at,
                updated_at=run.updated_at,
                total_gross_pay=sum(
                    (li.gross_pay for li in run.line_items), Decimal(0)
                ),
                employee_count=len(run.line_items),
            )
        )
    return summaries


@router.get(
    "/{run_id}",
    response_model=PayrollRunRead,
    summary="Get a specific payroll run",
)
async def get_payroll_run(
    business_id: UUID,
    run_id: UUID,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: GetPayrollRunUseCase = Depends(get_get_payroll_run_use_case),
) -> PayrollRunRead:
    cmd = GetPayrollRunCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        run_id=run_id,
    )
    run = await use_case.execute(cmd)

    return PayrollRunRead(
        id=run.id,
        business_id=run.business_id,
        period=PayrollPeriodRead(
            start_date=run.period.start_date,
            end_date=run.period.end_date,
        ),
        status=run.status,
        is_incomplete=run.is_incomplete,
        created_at=run.created_at,
        updated_at=run.updated_at,
        line_items=[PayrollLineItemRead.model_validate(li) for li in run.line_items],
    )
