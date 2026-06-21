from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentPrincipal, get_current_user
from app.holidays.application.commands import (
    CreateHolidayCommand,
    DeleteHolidayCommand,
    GetHolidayByDateCommand,
    ListHolidaysCommand,
    RenameHolidayCommand,
)
from app.holidays.application.use_cases import (
    CreateHolidayUseCase,
    ListHolidaysUseCase,
    RenameHolidayUseCase,
    DeleteHolidayUseCase,
    GetHolidayByDateUseCase,
)
from app.holidays.domain.exceptions import HolidayNotFoundError
from app.holidays.presentation.schemas import (
    HolidayCreate,
    HolidayUpdate,
    HolidayRead,
)
from app.holidays.presentation.dependencies import (
    get_create_holiday_use_case,
    get_list_holidays_use_case,
    get_rename_holiday_use_case,
    get_delete_holiday_use_case,
    get_get_holiday_by_date_use_case,
)


router = APIRouter()


@router.post(
    "",
    response_model=HolidayRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_holiday(
    business_id: UUID,
    payload: HolidayCreate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: CreateHolidayUseCase = Depends(get_create_holiday_use_case),
) -> HolidayRead:
    # business_id from path; current_user is available if you later want to check ownership
    cmd = CreateHolidayCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        date=payload.date,
        name=payload.name,
    )
    holiday = await use_case.execute(cmd)
    return HolidayRead.model_validate(holiday)


@router.get(
    "",
    response_model=list[HolidayRead],
)
async def list_holidays(
    business_id: UUID,
    year: int | None = None,
    month: int | None = None,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ListHolidaysUseCase = Depends(get_list_holidays_use_case),
) -> list[HolidayRead]:
    cmd = ListHolidaysCommand(
        business_id=business_id,
        year=year,
        month=month,
        owner_id=current_user.clerk_user_id,
    )
    holidays = await use_case.execute(cmd)
    return [HolidayRead.model_validate(h) for h in holidays]


@router.get(
    "/{holiday_date}",
    response_model=HolidayRead,
)
async def get_holiday_by_date(
    business_id: UUID,
    holiday_date: date,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: GetHolidayByDateUseCase = Depends(get_get_holiday_by_date_use_case),
) -> HolidayRead:
    cmd = GetHolidayByDateCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        date=holiday_date,
    )
    holiday = await use_case.execute(cmd)
    if holiday is None:
        # You can map HolidayNotFoundError globally instead if you prefer
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holiday not found",
        )
    return HolidayRead.model_validate(holiday)


@router.patch(
    "/{holiday_date}",
    response_model=HolidayRead,
)
async def update_holiday(
    business_id: UUID,
    holiday_date: date,
    payload: HolidayUpdate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: RenameHolidayUseCase = Depends(get_rename_holiday_use_case),
) -> HolidayRead:
    # PATCH semantics:
    # - If "name" not in payload, no fields to update → 400
    # - If name is string: new name
    # - If name is null or empty/whitespace: clear name
    if "name" not in payload.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    new_name = payload.name  # str | None, may already be normalized in schema

    cmd = RenameHolidayCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        date=holiday_date,
        new_name=new_name,
    )
    try:
        holiday = await use_case.execute(cmd)
    except HolidayNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holiday not found",
        )

    return HolidayRead.model_validate(holiday)


@router.delete(
    "/{holiday_date}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_holiday(
    business_id: UUID,
    holiday_date: date,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: DeleteHolidayUseCase = Depends(get_delete_holiday_use_case),
) -> None:
    cmd = DeleteHolidayCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        date=holiday_date,
    )
    await use_case.execute(cmd)
    # You can decide whether to raise 404 when nothing was deleted later
    return None
