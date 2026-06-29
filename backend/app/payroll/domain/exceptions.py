class PayrollException(Exception):
    """Base class for all payroll-related exceptions."""
    pass

class InvalidStateTransitionError(PayrollException):
    """Raised when an invalid state transition is attempted in the payroll process."""
    def __init__(self, message: str):
        super().__init__(message)

class InvalidPayrollConfigurationError(PayrollException):
    """Raised when the payroll configuration is invalid or inconsistent."""
    def __init__(self, message: str):
        super().__init__(message)

class PayrollCalculationError(PayrollException):
    """Raised when an error occurs during payroll calculation."""
    def __init__(self, message: str):
        super().__init__(message)