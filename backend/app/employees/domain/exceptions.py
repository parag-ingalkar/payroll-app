class EmployeeDomainError(Exception):
    """Base class for employee domain errors."""


class EmployeeNotFoundError(EmployeeDomainError):
    def __init__(self, message: str = "Employee not found.") -> None:
        super().__init__(message)


class InvalidEmployeeNameError(EmployeeDomainError):
    def __init__(self, message: str = "Invalid employee name.") -> None:
        super().__init__(message)
