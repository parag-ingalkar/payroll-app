class BusinessDomainError(Exception):
    """Base class for business domain errors."""


class InvalidWeeklyOffRulesError(BusinessDomainError):
    """Raised when weekly off rules violate aggregate invariants."""


class BusinessNotFoundError(BusinessDomainError):
    """Raised when a business is not found for a given ID and owner."""


class DuplicateBusinessError(BusinessDomainError):
    """Raised when a business with the same normalized name already exists for the owner."""
