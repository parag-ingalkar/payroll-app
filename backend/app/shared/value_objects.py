from enum import StrEnum


class WageType(StrEnum):
    DAILY = "daily"
    MONTHLY = "monthly"
    HOURLY = "hourly"


class SalaryBasis(StrEnum):
    WORKING_26_DAYS = "working_26_days"
    CALENDAR_DAYS = "calendar_days"


class Weekday(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    HALF_DAY = "half_day"
    ABSENT = "absent"
    PAID_LEAVE = "paid_leave"
    UNPAID_LEAVE = "unpaid_leave"
    PAID_HOLIDAY = "paid_holiday"
    UNPAID_HOLIDAY = "unpaid_holiday"
