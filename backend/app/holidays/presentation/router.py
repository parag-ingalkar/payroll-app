from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentPrincipal, get_current_user
from app.holidays.application.commands import (
    CreateHolidayCommand,
    DeleteHolidayCommand,
    GetHolidayCommand,
    ListHolidaysCommand,
    UpdateHolidayCommand,
)
from app.holidays.application.use_cases import (
    CreateHolidayUseCase,
    ListHolidaysUseCase,
    UpdateHolidayUseCase,
    DeleteHolidayUseCase,
    GetHolidayUseCase,
)
from app.holidays.presentation.schemas import (
    HolidayCreate,
    HolidayUpdate,
    HolidayResponse,
)
from app.holidays.presentation.dependencies import (
    get_create_holiday_use_case,
    get_list_holidays_use_case,
    get_update_holiday_use_case,
    get_delete_holiday_use_case,
    get_get_holiday_use_case,
)


router = APIRouter()


@router.post("", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
async def create_holiday(
    business_id: UUID,
    holiday_create: HolidayCreate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: CreateHolidayUseCase = Depends(get_create_holiday_use_case),
):
    command = CreateHolidayCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        holiday_date=holiday_create.holiday_date,
        holiday_name=holiday_create.holiday_name,
        is_paid=holiday_create.is_paid,
    )

    holiday = await use_case.execute(command)
    return HolidayResponse.model_validate(holiday)


@router.get("", response_model=list[HolidayResponse])
async def list_holidays(
    business_id: UUID,
    year: int | None = None,
    month: int | None = None,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ListHolidaysUseCase = Depends(get_list_holidays_use_case),
):
    command = ListHolidaysCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        year=year,
        month=month,
    )

    holidays = await use_case.execute(command)
    return [HolidayResponse.model_validate(h) for h in holidays]

@router.get("/{holiday_date}", response_model=HolidayResponse)
async def get_holiday(
    business_id: UUID,
    holiday_date: date,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: GetHolidayUseCase = Depends(get_get_holiday_use_case),
):
    command = GetHolidayCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        holiday_date=holiday_date,
    )

    holiday = await use_case.execute(command)

    return HolidayResponse.model_validate(holiday)


@router.patch("/{holiday_date}", response_model=HolidayResponse)
async def update_holiday(
    business_id: UUID,
    holiday_date: date,
    holiday_update: HolidayUpdate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: UpdateHolidayUseCase = Depends(get_update_holiday_use_case),
):
    command = UpdateHolidayCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        holiday_date=holiday_date,
        new_name=holiday_update.holiday_name,
        is_paid=holiday_update.is_paid,
    )

    holiday = await use_case.execute(command)
    return HolidayResponse.model_validate(holiday)

@router.delete("/{holiday_date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday(
    business_id: UUID,
    holiday_date: date,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: DeleteHolidayUseCase = Depends(get_delete_holiday_use_case),
):
    command = DeleteHolidayCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        holiday_date=holiday_date,
    )

    await use_case.execute(command)