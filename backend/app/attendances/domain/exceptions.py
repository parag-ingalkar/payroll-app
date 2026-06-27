class AttendanceDomainError(Exception):
    """Base class for attendance domain errors."""


class AttendanceAlreadyExistsError(AttendanceDomainError):
    def __init__(
        self,
        message: str = "Duplicate attendance record exists for the same business, employee, and date.",
    ) -> None:
        super().__init__(message)


class AttendanceNotFoundError(AttendanceDomainError):
    def __init__(self, message: str = "Attendance not found.") -> None:
        super().__init__(message)
        


class AttendanceOnHolidayError(AttendanceDomainError):
    def __init__(self, message: str = "Cannot mark attendance on a holiday.") -> None:
        super().__init__(message)


class AttendanceFutureDateError(AttendanceDomainError):
    def __init__(self, date: str) -> None:
        super().__init__(f"Cannot mark attendance for a future date: {date}.")
        self.date = date


class OvertimeNotAllowedError(AttendanceDomainError):
    def __init__(
        self,
        message: str = "Overtime hours can only be set when attendance is Present.",
    ) -> None:
        super().__init__(message)


class InactiveEmployeeAttendanceError(AttendanceDomainError):
    def __init__(self, employee_id: str) -> None:
        super().__init__(f"Cannot mark attendance for inactive employee {employee_id}.")
        self.employee_id = employee_id


class AttendanceOnWeeklyOffError(AttendanceDomainError):
    def __init__(self, date: str) -> None:
        super().__init__(f"Cannot mark attendance on a weekly off day: {date}.")
        self.date = date