class HolidayDomainError(Exception):
    """Base class for exceptions in the holidays domain."""


class HolidayAlreadyExistsError(HolidayDomainError):
    def __init__(self, business_id: str, date: str) -> None:
        super().__init__(
            f"Holiday already exists for business_id={business_id} on date={date}."
        )
        self.business_id = business_id
        self.date = date


class InvalidHolidayNameError(HolidayDomainError):
    """Raised when a holiday name is invalid (e.g., empty or whitespace)."""

    def __init__(self, message="Invalid holiday name"):
        super().__init__(message)


class HolidayNotFoundError(HolidayDomainError):
    """Raised when a holiday is not found for a given business and date."""

    def __init__(self, business_id: str, date: str):
        super().__init__(
            f"Holiday not found for business_id={business_id} on date={date}."
        )
        self.business_id = business_id
        self.date = date
