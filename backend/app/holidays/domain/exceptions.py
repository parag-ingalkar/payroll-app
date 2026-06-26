class HolidayDomainError(Exception):
    """Base class for exceptions in the holidays domain."""


class HolidayAlreadyExistsError(HolidayDomainError):
    """Raised when trying to create a holiday that already exists for a given business and date."""

    def __init__(self, message="Holiday already exists"):
        super().__init__(message)


class InvalidHolidayNameError(HolidayDomainError):
    """Raised when a holiday name is invalid (e.g., empty or whitespace)."""

    def __init__(self, message="Invalid holiday name"):
        super().__init__(message)


class HolidayNotFoundError(HolidayDomainError):
    """Raised when a holiday is not found for a given business and date."""

    def __init__(self, message="Holiday not found"):
        super().__init__(message)


class HolidayUpdateError(HolidayDomainError):
    """Raised when there is an error updating a holiday."""

    def __init__(self, message="Error updating holiday"):
        super().__init__(message)