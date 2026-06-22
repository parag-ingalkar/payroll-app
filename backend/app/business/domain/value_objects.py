import re
from enum import StrEnum


def normalize_whitespace(value: str) -> str:
    # Strip leading/trailing and collapse internal whitespace
    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_business_name_for_lookup(value: str) -> str:
    # Collapse whitespace then lowercase for case-insensitive uniqueness
    return normalize_whitespace(value).lower()


class WageType(StrEnum):
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"


class Weekday(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class SalaryBasis(StrEnum):
    CALENDAR_DAYS = "calendar_days"
    FIXED_30_DAYS = "fixed_30_days"
    WORKING_26_DAYS = "working_26_days"
