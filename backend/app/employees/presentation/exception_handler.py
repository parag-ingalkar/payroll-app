from fastapi import Request
from fastapi.responses import JSONResponse

from app.employees.domain.exceptions import (
    EmployeeNotFoundError,
    InvalidEmployeeNameError,
)


def register_employee_exception_handlers(app) -> None:
    @app.exception_handler(EmployeeNotFoundError)
    async def employee_not_found_exception_handler(
        request: Request,
        exc: EmployeeNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": {
                    "code": "employee_not_found",
                    "message": "Employee not found.",
                }
            },
        )

    @app.exception_handler(InvalidEmployeeNameError)
    async def invalid_employee_name_exception_handler(
        request: Request,
        exc: InvalidEmployeeNameError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "code": "invalid_employee_name",
                    "message": "Employee name is invalid.",
                    "fields": ["name"],
                }
            },
        )
