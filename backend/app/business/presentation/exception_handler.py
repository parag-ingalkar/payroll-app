# app/api_errors.py
from fastapi import Request
from fastapi.responses import JSONResponse

from app.business.domain.exceptions import (
    BusinessNotFoundError,
    DuplicateBusinessError,
    InvalidWeeklyOffRulesError,
)


def register_business_exception_handlers(app):
    @app.exception_handler(BusinessNotFoundError)
    async def business_not_found_exception_handler(
        request: Request, exc: BusinessNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": {
                    "code": "business_not_found",
                    "message": str(exc) or "Business not found.",
                }
            },
        )

    @app.exception_handler(DuplicateBusinessError)
    async def duplicate_business_exception_handler(
        request: Request, exc: DuplicateBusinessError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": {
                    "code": "duplicate_business_name",
                    "message": str(exc)
                    or "A business with this name already exists for this owner.",
                    "fields": ["name"],
                }
            },
        )

    @app.exception_handler(InvalidWeeklyOffRulesError)
    async def invalid_weekly_off_rules_exception_handler(
        request: Request, exc: InvalidWeeklyOffRulesError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "invalid_weekly_off_rules",
                    "message": str(exc)
                    or "Weekly off rules are invalid for this business.",
                    "fields": ["weekly_off_rules"],
                }
            },
        )
