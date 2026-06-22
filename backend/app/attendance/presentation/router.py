from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.attendance.application.commands import (
    BulkAttendanceEntry,
    BulkMarkAttendanceCommand,
    DeleteAttendanceCommand,
    GetAttendanceCommand,
    ListAttendanceByDateCommand,
    ListAttendanceByEmployeeCommand,
    MarkAllPresentCommand,
    MarkAttendanceCommand,
    UpdateAttendanceCommand,
)
from app.attendance.application.use_cases import (
    BulkMarkAttendanceUseCase,
    DeleteAttendanceUseCase,
    GetAttendanceUseCase,
    ListAttendanceByDateUseCase,
    ListAttendanceByEmployeeUseCase,
    MarkAllPresentUseCase,
    MarkAttendanceUseCase,
    UpdateAttendanceUseCase,
)
from app.attendance.domain.entities import AttendanceStatus
from app.attendance.presentation.dependencies import (
    get_bulk_mark_attendance_use_case,
    get_delete_attendance_use_case,
    get_get_attendance_use_case,
    get_list_attendance_by_date_use_case,
    get_list_attendance_by_employee_use_case,
    get_mark_all_present_use_case,
    get_mark_attendance_use_case,
    get_update_attendance_use_case,
)
from app.attendance.presentation.schemas import (
    AttendanceCreate,
    AttendanceRead,
    AttendanceUpdate,
    BulkMarkAttendanceRequest,
    MarkAllPresentRequest,
)
from app.core.dependencies import CurrentPrincipal, get_current_user

router = APIRouter()


@router.post(
    "",
    response_model=AttendanceRead,
    status_code=status.HTTP_201_CREATED,
)
async def mark_attendance(
    business_id: UUID,
    payload: AttendanceCreate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: MarkAttendanceUseCase = Depends(get_mark_attendance_use_case),
) -> AttendanceRead:
    cmd = MarkAttendanceCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=payload.employee_id,
        date=payload.date,
        status=payload.status,
        overtime_hours=payload.overtime_hours,
    )
    attendance = await use_case.execute(cmd)
    return AttendanceRead.model_validate(attendance)


@router.post(
    "/bulk",
    response_model=list[AttendanceRead],
    status_code=status.HTTP_200_OK,
)
async def bulk_mark_attendance(
    business_id: UUID,
    payload: BulkMarkAttendanceRequest,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: BulkMarkAttendanceUseCase = Depends(get_bulk_mark_attendance_use_case),
) -> list[AttendanceRead]:
    cmd = BulkMarkAttendanceCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        date=payload.date,
        entries=[
            BulkAttendanceEntry(
                employee_id=item.employee_id,
                status=item.status,
                overtime_hours=item.overtime_hours,
            )
            for item in payload.entries
        ],
    )
    records = await use_case.execute(cmd)
    return [AttendanceRead.model_validate(r) for r in records]


@router.post(
    "/mark-all-present",
    response_model=list[AttendanceRead],
    status_code=status.HTTP_200_OK,
)
async def mark_all_present(
    business_id: UUID,
    payload: MarkAllPresentRequest,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: MarkAllPresentUseCase = Depends(get_mark_all_present_use_case),
) -> list[AttendanceRead]:
    cmd = MarkAllPresentCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        date=payload.date,
    )
    records = await use_case.execute(cmd)
    return [AttendanceRead.model_validate(r) for r in records]


@router.get(
    "/by-date",
    response_model=list[AttendanceRead],
)
async def list_attendance_by_date(
    business_id: UUID,
    attendance_date: date = Query(..., alias="date"),
    employee_id: UUID | None = None,
    attendance_status: AttendanceStatus | None = Query(default=None, alias="status"),
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ListAttendanceByDateUseCase = Depends(
        get_list_attendance_by_date_use_case
    ),
) -> list[AttendanceRead]:
    cmd = ListAttendanceByDateCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        date=attendance_date,
        employee_id=employee_id,
        status=attendance_status,
    )
    records = await use_case.execute(cmd)
    return [AttendanceRead.model_validate(r) for r in records]


@router.get(
    "/by-employee/{employee_id}",
    response_model=list[AttendanceRead],
)
async def list_attendance_by_employee(
    business_id: UUID,
    employee_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    attendance_status: AttendanceStatus | None = Query(default=None, alias="status"),
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: ListAttendanceByEmployeeUseCase = Depends(
        get_list_attendance_by_employee_use_case
    ),
) -> list[AttendanceRead]:
    cmd = ListAttendanceByEmployeeCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        status=attendance_status,
    )
    records = await use_case.execute(cmd)
    return [AttendanceRead.model_validate(r) for r in records]


@router.get(
    "/{employee_id}/{attendance_date}",
    response_model=AttendanceRead,
)
async def get_attendance(
    business_id: UUID,
    employee_id: UUID,
    attendance_date: date,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: GetAttendanceUseCase = Depends(get_get_attendance_use_case),
) -> AttendanceRead:
    cmd = GetAttendanceCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
        date=attendance_date,
    )
    attendance = await use_case.execute(cmd)
    return AttendanceRead.model_validate(attendance)


@router.patch(
    "/{employee_id}/{attendance_date}",
    response_model=AttendanceRead,
)
async def update_attendance(
    business_id: UUID,
    employee_id: UUID,
    attendance_date: date,
    payload: AttendanceUpdate,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: UpdateAttendanceUseCase = Depends(get_update_attendance_use_case),
) -> AttendanceRead:
    if not payload.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "no_fields_to_update",
                "message": "No fields to update.",
            },
        )
    cmd = UpdateAttendanceCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
        date=attendance_date,
        fields_to_update=frozenset(payload.model_fields_set),
        status=payload.status,
        overtime_hours=payload.overtime_hours,
    )
    attendance = await use_case.execute(cmd)
    return AttendanceRead.model_validate(attendance)


@router.delete(
    "/{employee_id}/{attendance_date}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attendance(
    business_id: UUID,
    employee_id: UUID,
    attendance_date: date,
    current_user: CurrentPrincipal = Depends(get_current_user),
    use_case: DeleteAttendanceUseCase = Depends(get_delete_attendance_use_case),
) -> None:
    cmd = DeleteAttendanceCommand(
        business_id=business_id,
        owner_id=current_user.clerk_user_id,
        employee_id=employee_id,
        date=attendance_date,
    )
    await use_case.execute(cmd)
    return None
