# app/holidays/presentation/exception_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse

from app.holidays.domain.exceptions import (
    HolidayNotFoundError,
    HolidayAlreadyExistsError,
    InvalidHolidayNameError,
)


def register_holiday_exception_handlers(app):
    @app.exception_handler(HolidayNotFoundError)
    async def holiday_not_found_exception_handler(
        request: Request,
        exc: HolidayNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": {
                    "code": "holiday_not_found",
                    "message": str(exc) or "Holiday not found.",
                }
            },
        )

    @app.exception_handler(HolidayAlreadyExistsError)
    async def holiday_already_exists_exception_handler(
        request: Request,
        exc: HolidayAlreadyExistsError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": {
                    "code": "holiday_already_exists",
                    "message": str(exc)
                    or "A holiday already exists for this business on this date.",
                    "fields": ["date"],
                }
            },
        )

    @app.exception_handler(InvalidHolidayNameError)
    async def invalid_holiday_name_exception_handler(
        request: Request,
        exc: InvalidHolidayNameError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "invalid_holiday_name",
                    "message": str(exc) or "Holiday name is invalid.",
                    "fields": ["name"],
                }
            },
        )