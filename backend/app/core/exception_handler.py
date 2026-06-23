from app.attendance.presentation.exception_handler import (
    register_attendance_exception_handlers,
)
from app.business.presentation.exception_handler import (
    register_business_exception_handlers,
)
from app.employees.presentation.exception_handler import (
    register_employee_exception_handlers,
)
from app.holidays.presentation.exception_handler import (
    register_holiday_exception_handlers,
)
from app.payroll.presentation.exception_handler import (
    register_payroll_exception_handlers,
)


def register_exception_handlers(app) -> None:
    register_business_exception_handlers(app)
    register_holiday_exception_handlers(app)
    register_employee_exception_handlers(app)
    register_attendance_exception_handlers(app)
    register_payroll_exception_handlers(app)
