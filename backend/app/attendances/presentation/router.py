from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentPrincipal, get_current_user
from app.attendances.application.commands import (
    UpsertAttendanceCommand,
    DeleteAttendanceCommand,
    ListAttendancesByDateCommand,
    ListAttendancesByMonthCommand,
    GetEmployeeAttendanceDayCommand,
    GetEmployeeAttendanceMonthCommand,
    BulkUpsertAttendanceCommand,
    BulkAttendanceEntry as BulkAttendanceEntryCommand,
)
from app.attendances.application.use_cases import (
    UpsertAttendanceUseCase,
    DeleteAttendanceUseCase,
    ListAttendancesByDateUseCase,
    ListAttendancesByMonthUseCase,
    GetEmployeeAttendanceDayUseCase,
    GetEmployeeAttendanceMonthUseCase,
    BulkUpsertAttendanceUseCase,
)
from app.attendances.presentation.dependencies import (
    get_upsert_attendance_use_case,
    get_delete_attendance_use_case,
    get_list_attendances_by_date_use_case,
    get_list_attendances_by_month_use_case,
    get_get_employee_attendance_day_use_case,
    get_get_employee_attendance_month_use_case,
    get_bulk_upsert_attendance_use_case,
)
from app.attendances.presentation.schemas import (
    # AttendanceCreate,
    # AttendanceUpdate,
    AttendanceUpsert,
    AttendanceRead,
    BulkAttendanceCreate,
)
from app.shared.value_objects import AttendanceStatus

router = APIRouter()


@router.post(
    "/attendances",
    response_model=AttendanceRead,
    status_code=status.HTTP_200_OK,
)
async def upsert_attendance(
    business_id: UUID,
    payload: AttendanceUpsert,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: UpsertAttendanceUseCase = Depends(get_upsert_attendance_use_case),
) -> AttendanceRead:

    cmd = UpsertAttendanceCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=payload.employee_id,
        date=payload.date,
        status=payload.status,
        overtime_hours=payload.overtime_hours,
        marked_by=current_user.clerk_user_id,
        notes=payload.notes,
    )

    attendance = await use_case.execute(cmd)
    return AttendanceRead.model_validate(attendance)


@router.post(
    "/attendances/bulk",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def bulk_upsert_attendance(
    business_id: UUID,
    payload: BulkAttendanceCreate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: BulkUpsertAttendanceUseCase = Depends(
        get_bulk_upsert_attendance_use_case
    ),
) -> None:
    """
    Bulk upsert attendance for a specific date (grid-style).
    """

    entries = [
        BulkAttendanceEntryCommand(
            employee_id=entry.employee_id,
            status=entry.status,
            overtime_hours=entry.overtime_hours,
            notes=entry.notes,
        )
        for entry in payload.entries
    ]

    cmd = BulkUpsertAttendanceCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        date=payload.date,
        marked_by=current_user.clerk_user_id,
        entries=entries,
    )

    await use_case.execute(cmd)


@router.get(
    "/attendances/by-date",
    response_model=list[AttendanceRead],
)
async def list_attendances_by_date(
    business_id: UUID,
    date_: date = Query(..., alias="date"),
    status_: AttendanceStatus | None = Query(None, alias="status"),
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ListAttendancesByDateUseCase = Depends(
        get_list_attendances_by_date_use_case
    ),
) -> list[AttendanceRead]:
    """
    List attendances for a business on a given date.
    """

    cmd = ListAttendancesByDateCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        date=date_,
        status=status_,
    )
    attendances = await use_case.execute(cmd)
    return [AttendanceRead.model_validate(a) for a in attendances]


@router.get(
    "/attendances/by-month",
    response_model=list[AttendanceRead],
)
async def list_attendances_by_month(
    business_id: UUID,
    year: int = Query(...),
    month: int = Query(...),
    status_: AttendanceStatus | None = Query(None, alias="status"),
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ListAttendancesByMonthUseCase = Depends(
        get_list_attendances_by_month_use_case
    ),
) -> list[AttendanceRead]:
    """
    List attendances for a business in a given month.
    """

    cmd = ListAttendancesByMonthCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        year=year,
        month=month,
        status=status_,
    )
    attendances = await use_case.execute(cmd)
    return [AttendanceRead.model_validate(a) for a in attendances]


@router.get(
    "/employees/{employee_id}/attendances/by-day",
    response_model=AttendanceRead | None,
)
async def get_employee_attendance_day(
    business_id: UUID,
    employee_id: UUID,
    date_: date = Query(..., alias="date"),
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: GetEmployeeAttendanceDayUseCase = Depends(
        get_get_employee_attendance_day_use_case
    ),
) -> AttendanceRead | None:
    """
    Get a single employee's attendance for a specific day.
    """

    cmd = GetEmployeeAttendanceDayCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
        date=date_,
    )
    attendance = await use_case.execute(cmd)
    if attendance is None:
        return None
    return AttendanceRead.model_validate(attendance)


@router.get(
    "/employees/{employee_id}/attendances/by-month",
    response_model=list[AttendanceRead],
)
async def get_employee_attendance_month(
    business_id: UUID,
    employee_id: UUID,
    year: int = Query(...),
    month: int = Query(...),
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: GetEmployeeAttendanceMonthUseCase = Depends(
        get_get_employee_attendance_month_use_case
    ),
) -> list[AttendanceRead]:
    """
    Get a single employee's attendance for a given month.
    """

    cmd = GetEmployeeAttendanceMonthCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
        year=year,
        month=month,
    )
    attendances = await use_case.execute(cmd)
    return [AttendanceRead.model_validate(a) for a in attendances]


@router.delete(
    "/attendances",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attendance(
    business_id: UUID,
    employee_id: UUID = Query(...),
    date_: date = Query(..., alias="date"),
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: DeleteAttendanceUseCase = Depends(get_delete_attendance_use_case),
) -> None:
    """
    Delete a single employee's attendance for a specific date.
    """

    cmd = DeleteAttendanceCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
        date=date_,
    )
    await use_case.execute(cmd)
