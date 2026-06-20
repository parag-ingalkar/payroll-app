# from dataclasses import dataclass
# from decimal import Decimal
import re


def normalize_whitespace(value: str) -> str:
    # Strip leading/trailing and collapse internal whitespace
    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_business_name_for_lookup(value: str) -> str:
    # Collapse whitespace then lowercase for case-insensitive uniqueness
    return normalize_whitespace(value).lower()


# @dataclass(frozen=True)
# class BusinessName:
#     value: str

#     def __post_init__(self):
#         normalized = normalize_whitespace(self.value)
#         if not normalized:
#             raise ValueError("Business name cannot be empty or whitespace.")
#         object.__setattr__(self, "value", normalized)

#     def lower(self) -> str:
#         return self.value.lower()

#     def __repr__(self) -> str:
#         return self.value


# @dataclass(frozen=True)
# class WorkingHoursPerDay:
#     value: Decimal

#     def __post_init__(self):
#         if self.value <= 0 or self.value > Decimal("24"):
#             raise ValueError("Working hours per day must be > 0 and ≤ 24.")


# @dataclass(frozen=True)
# class OvertimeMultiplier:
#     value: Decimal

#     def __post_init__(self):
#         if self.value < 1:
#             raise ValueError("Overtime multiplier must be at least 1.")
