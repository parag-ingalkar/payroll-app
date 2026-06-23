from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.payroll.domain.exceptions import PayrollRunNotFoundError


def register_payroll_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PayrollRunNotFoundError)
    async def payroll_run_not_found_handler(request, exc: PayrollRunNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "detail": {
                    "code": "payroll_run_not_found",
                    "message": str(exc) or "Payroll run not found.",
                }
            },
        )
