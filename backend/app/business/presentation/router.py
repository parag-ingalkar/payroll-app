# app/business/presentation/router.py
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.business.application.commands import (
    CreateBusinessCommand,
    UpdateBusinessCommand,
    ReplaceWeeklyOffRulesCommand,
    WeeklyOffRuleInput,
)
from app.business.application.use_cases import (
    CreateBusinessUseCase,
    ListBusinessesUseCase,
    GetBusinessUseCase,
    UpdateBusinessUseCase,
    DeleteBusinessUseCase,
    GetWeeklyOffRulesUseCase,
    ReplaceWeeklyOffRulesUseCase,
)
from app.business.presentation.schemas import (
    BusinessCreate,
    BusinessUpdate,
    BusinessRead,
    BusinessWeeklyOffRuleRead,
    BusinessWeeklyOffRuleCreate,
)
from app.business.presentation.dependencies import (
    get_create_business_use_case,
    get_list_businesses_use_case,
    get_get_business_use_case,
    get_update_business_use_case,
    get_delete_business_use_case,
    get_get_weekly_off_rules_use_case,
    get_replace_weekly_off_rules_use_case,
)
from app.core.dependencies import get_current_user, CurrentPrincipal

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.post(
    "",
    response_model=BusinessRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_business(
    payload: BusinessCreate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: CreateBusinessUseCase = Depends(get_create_business_use_case),
) -> BusinessRead:
    business = await use_case.execute(
        CreateBusinessCommand(
            owner_id=current_user.clerk_user_id,
            name=payload.name,
            default_wage_type=payload.default_wage_type,
            default_working_hours_per_day=payload.default_working_hours_per_day,
            default_overtime_multiplier=payload.default_overtime_multiplier,
            payroll_start_day=payload.payroll_start_day,
            weekly_off_rules=[
                WeeklyOffRuleInput(
                    weekday=rule.weekday,
                    week_of_month=rule.week_of_month,
                )
                for rule in payload.weekly_off_rules
            ],
        )
    )
    return BusinessRead.model_validate(business)


@router.get("", response_model=list[BusinessRead])
async def list_businesses(
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ListBusinessesUseCase = Depends(get_list_businesses_use_case),
) -> list[BusinessRead]:
    businesses = await use_case.execute(owner_id=current_user.clerk_user_id)
    return [BusinessRead.model_validate(b) for b in businesses]


@router.get("/{business_id}", response_model=BusinessRead)
async def get_business(
    business_id: UUID,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: GetBusinessUseCase = Depends(get_get_business_use_case),
) -> BusinessRead:
    business = await use_case.execute(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
    )
    return BusinessRead.model_validate(business)


@router.patch("/{business_id}", response_model=BusinessRead)
async def update_business(
    business_id: UUID,
    payload: BusinessUpdate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: UpdateBusinessUseCase = Depends(get_update_business_use_case),
) -> BusinessRead:
    business = await use_case.execute(
        UpdateBusinessCommand(
            business_id=business_id,
            owner_id=current_user.clerk_user_id,
            name=payload.name,
            default_wage_type=payload.default_wage_type,
            default_working_hours_per_day=payload.default_working_hours_per_day,
            default_overtime_multiplier=payload.default_overtime_multiplier,
            payroll_start_day=payload.payroll_start_day,
        )
    )
    return BusinessRead.model_validate(business)


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: UUID,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: DeleteBusinessUseCase = Depends(get_delete_business_use_case),
) -> None:
    await use_case.execute(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
    )


@router.get(
    "/{business_id}/weekly-off-rules", response_model=list[BusinessWeeklyOffRuleRead]
)
async def get_weekly_off_rules(
    business_id: UUID,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: GetWeeklyOffRulesUseCase = Depends(get_get_weekly_off_rules_use_case),
) -> list[BusinessWeeklyOffRuleRead]:
    rules = await use_case.execute(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
    )
    return [BusinessWeeklyOffRuleRead.model_validate(rule) for rule in rules]


@router.put("/{business_id}/weekly-off-rules", response_model=BusinessRead)
async def replace_weekly_off_rules(
    business_id: UUID,
    payload: list[BusinessWeeklyOffRuleCreate],
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ReplaceWeeklyOffRulesUseCase = Depends(
        get_replace_weekly_off_rules_use_case
    ),
) -> BusinessRead:
    business = await use_case.execute(
        ReplaceWeeklyOffRulesCommand(
            business_id=business_id,
            owner_id=current_user.clerk_user_id,
            weekly_off_rules=[
                WeeklyOffRuleInput(
                    weekday=rule.weekday,
                    week_of_month=rule.week_of_month,
                )
                for rule in payload
            ],
        )
    )
    return BusinessRead.model_validate(business)
