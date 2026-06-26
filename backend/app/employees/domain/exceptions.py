class EmployeeDomainError(Exception):
    """Base class for employee domain errors."""


class EmployeeNotFoundError(EmployeeDomainError):
    def __init__(self, business_id: str, employee_id: str) -> None:
        super().__init__(
            f"Employee with id {employee_id} not found for business {business_id}."
        )
        self.business_id = business_id
        self.employee_id = employee_id


class InvalidEmployeeNameError(EmployeeDomainError):
    def __init__(self, message: str = "Invalid employee name.") -> None:
        super().__init__(message)
