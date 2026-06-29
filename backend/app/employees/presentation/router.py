from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentPrincipal, get_current_user
from app.employees.application.commands import (
    ActivateEmployeeCommand,
    CreateEmployeeCommand,
    DeactivateEmployeeCommand,
    DeleteEmployeeCommand,
    GetEmployeeByIdCommand,
    ListEmployeesCommand,
    UpdateEmployeeCommand,
)
from app.employees.application.use_cases import (
    ActivateEmployeeUseCase,
    CreateEmployeeUseCase,
    DeactivateEmployeeUseCase,
    DeleteEmployeeUseCase,
    GetEmployeeByIdUseCase,
    ListEmployeesUseCase,
    UpdateEmployeeUseCase,
)
from app.employees.presentation.dependencies import (
    get_activate_employee_use_case,
    get_create_employee_use_case,
    get_deactivate_employee_use_case,
    get_delete_employee_use_case,
    get_get_employee_by_id_use_case,
    get_list_employees_use_case,
    get_update_employee_use_case,
)
from app.employees.presentation.schemas import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeUpdate,
)

router = APIRouter()


@router.post(
    "",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    business_id: UUID,
    payload: EmployeeCreate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: CreateEmployeeUseCase = Depends(get_create_employee_use_case),
) -> EmployeeRead:
    cmd = CreateEmployeeCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        name=payload.name,
        designation=payload.designation,
        wage_type=payload.wage_type,
        salary_basis=payload.salary_basis,
        wage_rate=payload.wage_rate,
        working_hours_per_day=payload.working_hours_per_day,
        overtime_multiplier=payload.overtime_multiplier,
    )
    employee = await use_case.execute(cmd)
    return EmployeeRead.model_validate(employee)


@router.get(
    "",
    response_model=list[EmployeeRead],
)
async def list_employees(
    business_id: UUID,
    is_active: bool | None = None,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ListEmployeesUseCase = Depends(get_list_employees_use_case),
) -> list[EmployeeRead]:
    cmd = ListEmployeesCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        is_active=is_active,
    )
    employees = await use_case.execute(cmd)
    return [EmployeeRead.model_validate(e) for e in employees]


@router.get(
    "/{employee_id}",
    response_model=EmployeeRead,
)
async def get_employee(
    business_id: UUID,
    employee_id: UUID,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: GetEmployeeByIdUseCase = Depends(get_get_employee_by_id_use_case),
) -> EmployeeRead:
    cmd = GetEmployeeByIdCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
    )
    employee = await use_case.execute(cmd)
    return EmployeeRead.model_validate(employee)


@router.patch(
    "/{employee_id}",
    response_model=EmployeeRead,
)
async def update_employee(
    business_id: UUID,
    employee_id: UUID,
    payload: EmployeeUpdate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: UpdateEmployeeUseCase = Depends(get_update_employee_use_case),
) -> EmployeeRead:
    if not payload.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "no_fields_to_update",
                "message": "No fields to update.",
            },
        )

    cmd = UpdateEmployeeCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
        fields_to_update=frozenset(payload.model_fields_set),
        name=payload.name,
        designation=payload.designation,
        wage_type=payload.wage_type,
        salary_basis=payload.salary_basis,
        wage_rate=payload.wage_rate,
        working_hours_per_day=payload.working_hours_per_day,
        overtime_multiplier=payload.overtime_multiplier,
    )
    employee = await use_case.execute(cmd)
    return EmployeeRead.model_validate(employee)


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_employee(
    business_id: UUID,
    employee_id: UUID,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: DeleteEmployeeUseCase = Depends(get_delete_employee_use_case),
) -> None:
    cmd = DeleteEmployeeCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
    )
    await use_case.execute(cmd)
    return None


@router.patch("/{employee_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_employee(
    business_id: UUID,
    employee_id: UUID,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: DeactivateEmployeeUseCase = Depends(get_deactivate_employee_use_case),
) -> None:
    cmd = DeactivateEmployeeCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
    )
    await use_case.execute(cmd)
    return None


@router.patch("/{employee_id}/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_employee(
    business_id: UUID,
    employee_id: UUID,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ActivateEmployeeUseCase = Depends(get_activate_employee_use_case),
) -> None:
    cmd = ActivateEmployeeCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
    )
    await use_case.execute(cmd)
    return None