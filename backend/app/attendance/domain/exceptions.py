class AttendanceDomainError(Exception):
    """Base class for attendance domain errors."""


class AttendanceAlreadyExistsError(AttendanceDomainError):
    def __init__(self, employee_id: str, date: str) -> None:
        super().__init__(
            f"Attendance already exists for employee {employee_id} on {date}."
        )
        self.employee_id = employee_id
        self.date = date


class AttendanceNotFoundError(AttendanceDomainError):
    def __init__(self, employee_id: str, date: str) -> None:
        super().__init__(f"Attendance not found for employee {employee_id} on {date}.")
        self.employee_id = employee_id
        self.date = date


class AttendanceOnHolidayError(AttendanceDomainError):
    def __init__(self, date: str) -> None:
        super().__init__(f"Cannot mark attendance on a holiday: {date}.")
        self.date = date


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
