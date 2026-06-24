class BusinessException(Exception):
    """Base class for all business-related exceptions."""

    pass


class InvalidWeeklyOffRulesError(BusinessException):
    """Raised when weekly off rules violate aggregate invariants."""

    def __init__(self, message: str = "Invalid weekly off rules.") -> None:
        super().__init__(message)


class BusinessNotFoundError(BusinessException):
    """Raised when a business is not found for a given ID and owner."""

    def __init__(self, message: str = "Business not found.") -> None:
        super().__init__(message)


class DuplicateBusinessError(BusinessException):
    """Raised when a business with the same normalized name already exists for the owner."""

    def __init__(self, message: str = "Duplicate business found.") -> None:
        super().__init__(message)
