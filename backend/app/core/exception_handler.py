from app.businesses.presentation.exception_handler import (
    register_business_exception_handlers,
)
from app.holidays.presentation.exception_handler import (
    register_holiday_exception_handlers,
)
from app.employees.presentation.exception_handlers import (
    register_employee_exception_handlers,
)


def register_exception_handlers(app) -> None:
    register_business_exception_handlers(app)
    register_holiday_exception_handlers(app)
    register_employee_exception_handlers(app)
