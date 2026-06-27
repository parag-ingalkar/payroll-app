from fastapi import Request
from fastapi.responses import JSONResponse

from app.attendances.domain.exceptions import (
    AttendanceDomainError,
    AttendanceNotFoundError,
    AttendanceOnHolidayError,
    AttendanceFutureDateError,
    InactiveEmployeeAttendanceError,
    AttendanceOnWeeklyOffError,
)


def register_attendance_exception_handlers(app) -> None:
    @app.exception_handler(AttendanceNotFoundError)
    async def attendance_not_found_exception_handler(
        request: Request,
        exc: AttendanceNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": {
                    "code": "attendance_not_found",
                    "message": "Attendance record not found.",
                }
            },
        )

    @app.exception_handler(AttendanceOnHolidayError)
    async def attendance_on_holiday_exception_handler(
        request: Request,
        exc: AttendanceOnHolidayError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "attendance_on_holiday",
                    "message": str(exc),
                }
            },
        )

    @app.exception_handler(AttendanceOnWeeklyOffError)
    async def attendance_on_weekly_off_exception_handler(
        request: Request,
        exc: AttendanceOnWeeklyOffError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "attendance_on_weekly_off",
                    "message": str(exc),
                }
            },
        )

    @app.exception_handler(AttendanceFutureDateError)
    async def attendance_future_date_exception_handler(
        request: Request,
        exc: AttendanceFutureDateError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "attendance_future_date",
                    "message": str(exc),
                }
            },
        )

    @app.exception_handler(InactiveEmployeeAttendanceError)
    async def inactive_employee_attendance_exception_handler(
        request: Request,
        exc: InactiveEmployeeAttendanceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "inactive_employee_attendance",
                    "message": str(exc),
                }
            },
        )

    @app.exception_handler(AttendanceDomainError)
    async def generic_attendance_domain_exception_handler(
        request: Request,
        exc: AttendanceDomainError,
    ) -> JSONResponse:
        # Fallback for any other attendance domain errors
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "attendance_error",
                    "message": str(exc),
                }
            },
        )