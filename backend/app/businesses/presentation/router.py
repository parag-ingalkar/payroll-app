from fastapi import Depends, APIRouter, status
from uuid import UUID
from app.businesses.application.commands import (
    CreateBusinessCommand,
    UpdateBusinessCommand,
    ReplaceWeeklyOffRulesCommand,
    WeeklyOffRuleInput,
)

from app.businesses.application.use_cases import (
    CreateBusinessUseCase,
    ListBusinessesUseCase,
    GetBusinessUseCase,
    DeleteBusinessUseCase,
    ReplaceWeeklyOffRulesUseCase,
    UpdateBusinessUseCase,
)

from app.businesses.presentation.dependencies import (
    get_create_business_use_case,
    get_list_businesses_use_case,
    get_get_business_use_case,
    get_delete_business_use_case,
    get_replace_weekly_off_rules_use_case,
    get_update_business_use_case,
)

from app.businesses.presentation.schemas import (
    BusinessCreate,
    BusinessUpdate,
    BusinessResponse,
    WeeklyOffRuleResponse,
)

from app.core.dependencies import CurrentPrincipal, get_current_user


router = APIRouter()


@router.post(
    "/businesses", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED
)
async def create_business(
    payload: BusinessCreate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: CreateBusinessUseCase = Depends(get_create_business_use_case),
):
    cmd = CreateBusinessCommand(
        owner_id=current_user.clerk_user_id,
        name=payload.name,
        default_salary_basis=payload.default_salary_basis,
        payroll_start_day=payload.payroll_start_day,
        default_wage_type=payload.default_wage_type,
        default_working_hours_per_day=payload.default_working_hours_per_day,
        default_overtime_multiplier=payload.default_overtime_multiplier,
        weekly_off_rules=[
            WeeklyOffRuleInput(weekday=rule.weekday)
            for rule in payload.weekly_off_rules
        ],
    )
    business = await use_case.execute(cmd)
    return BusinessResponse.model_validate(business)


@router.get("/businesses", response_model=list[BusinessResponse])
async def list_businesses(
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ListBusinessesUseCase = Depends(get_list_businesses_use_case),
):
    businesses = await use_case.execute(owner_id=current_user.clerk_user_id)
    return [BusinessResponse.model_validate(business) for business in businesses]


@router.get("/businesses/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: UUID,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: GetBusinessUseCase = Depends(get_get_business_use_case),
):
    business = await use_case.execute(
        business_id=business_id, owner_id=current_user.clerk_user_id
    )
    return BusinessResponse.model_validate(business)


@router.patch("/businesses/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: UUID,
    payload: BusinessUpdate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: UpdateBusinessUseCase = Depends(get_update_business_use_case),
):
    cmd = UpdateBusinessCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        name=payload.name,
        default_salary_basis=payload.default_salary_basis,
        payroll_start_day=payload.payroll_start_day,
        default_wage_type=payload.default_wage_type,
        default_working_hours_per_day=payload.default_working_hours_per_day,
        default_overtime_multiplier=payload.default_overtime_multiplier,
    )
    business = await use_case.execute(cmd)
    return BusinessResponse.model_validate(business)


@router.get(
    "/businesses/{business_id}/weekly-off-rules",
    response_model=list[WeeklyOffRuleResponse],
)
async def get_weekly_off_rules(
    business_id: UUID,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: GetBusinessUseCase = Depends(get_get_business_use_case),
):
    business = await use_case.execute(
        business_id=business_id, owner_id=current_user.clerk_user_id
    )
    return [
        WeeklyOffRuleResponse.model_validate(rule) for rule in business.weekly_off_rules
    ]


@router.put(
    "/businesses/{business_id}/weekly-off-rules",
    response_model=list[WeeklyOffRuleResponse],
)
async def replace_weekly_off_rules(
    business_id: UUID,
    payload: list[WeeklyOffRuleInput],
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ReplaceWeeklyOffRulesUseCase = Depends(
        get_replace_weekly_off_rules_use_case
    ),
):
    cmd = ReplaceWeeklyOffRulesCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        weekly_off_rules=payload,
    )
    business = await use_case.execute(cmd)
    return [
        WeeklyOffRuleResponse.model_validate(rule) for rule in business.weekly_off_rules
    ]


@router.delete("/businesses/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: UUID,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: DeleteBusinessUseCase = Depends(get_delete_business_use_case),
):
    await use_case.execute(business_id=business_id, owner_id=current_user.clerk_user_id)
