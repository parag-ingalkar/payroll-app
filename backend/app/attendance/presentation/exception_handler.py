from fastapi import Request
from fastapi.responses import JSONResponse

from app.attendance.domain.exceptions import (
    AttendanceAlreadyExistsError,
    AttendanceFutureDateError,
    AttendanceNotFoundError,
    AttendanceOnHolidayError,
    AttendanceOnWeeklyOffError,
    InactiveEmployeeAttendanceError,
    OvertimeNotAllowedError,
)


def register_attendance_exception_handlers(app) -> None:
    @app.exception_handler(AttendanceAlreadyExistsError)
    async def attendance_already_exists_handler(
        request: Request, exc: AttendanceAlreadyExistsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": {
                    "code": "attendance_already_exists",
                    "message": str(exc),
                    "fields": ["employee_id", "date"],
                }
            },
        )

    @app.exception_handler(AttendanceNotFoundError)
    async def attendance_not_found_handler(
        request: Request, exc: AttendanceNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": {
                    "code": "attendance_not_found",
                    "message": str(exc),
                }
            },
        )

    @app.exception_handler(AttendanceOnHolidayError)
    async def attendance_on_holiday_handler(
        request: Request, exc: AttendanceOnHolidayError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": {
                    "code": "attendance_on_holiday",
                    "message": str(exc),
                    "fields": ["date"],
                }
            },
        )

    @app.exception_handler(AttendanceFutureDateError)
    async def attendance_future_date_handler(
        request: Request, exc: AttendanceFutureDateError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "attendance_future_date",
                    "message": str(exc),
                    "fields": ["date"],
                }
            },
        )

    @app.exception_handler(OvertimeNotAllowedError)
    async def overtime_not_allowed_handler(
        request: Request, exc: OvertimeNotAllowedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "overtime_not_allowed",
                    "message": str(exc),
                    "fields": ["overtime_hours"],
                }
            },
        )

    @app.exception_handler(InactiveEmployeeAttendanceError)
    async def inactive_employee_attendance_handler(
        request: Request, exc: InactiveEmployeeAttendanceError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "inactive_employee_attendance",
                    "message": str(exc),
                    "fields": ["employee_id"],
                }
            },
        )

    @app.exception_handler(AttendanceOnWeeklyOffError)
    async def attendance_on_weekly_off_handler(
        request: Request, exc: AttendanceOnWeeklyOffError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": {
                    "code": "attendance_on_weekly_off",
                    "message": str(exc),
                    "fields": ["date"],
                }
            },
        )
