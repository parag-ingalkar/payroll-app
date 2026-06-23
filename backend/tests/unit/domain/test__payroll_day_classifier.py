# tests/unit/domain/test__payroll_day_classifier.py
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.attendance.domain.entities import Attendance, AttendanceStatus
from app.business.domain.entities import Business, WageType, Weekday, WeeklyOffRule
from app.business.domain.value_objects import SalaryBasis
from app.employees.domain.entities import Employee
from app.holidays.domain.entities import Holiday
from app.payroll.domain.day_classifier import DayClassifier, EmployeePayrollContext
from app.payroll.domain.value_objects import PayDayType, PayrollPeriod

# ── Helpers ────────────────────────────────────────────────────────────────────


def make_employee(business_id, wage_type=WageType.MONTHLY) -> Employee:
    return Employee.create(
        id=uuid4(),
        business_id=business_id,
        name="Test Employee",
        designation="Engineer",
        wage_type=wage_type,
        salary_basis=SalaryBasis.WORKING_26_DAYS,
        wage_rate=Decimal("50000"),
        working_hours_per_day=Decimal("8"),
        overtime_multiplier=Decimal("1.5"),
    )


def make_attendance(
    employee: Employee,
    d: date,
    status: AttendanceStatus,
    overtime_hours: Decimal = Decimal("0"),
) -> Attendance:
    return Attendance.create(
        id=uuid4(),
        business_id=employee.business_id,
        employee_id=employee.id,
        date=d,
        status=status,
        overtime_hours=overtime_hours,
    )


def make_context(employee, attendance_records=None, holidays=None, business=None):
    if business is None:
        business = Business.create(
            owner_id="owner",
            name="Test Biz",
            default_wage_type=WageType.MONTHLY,
            default_working_hours_per_day=Decimal("8"),
            default_overtime_multiplier=Decimal("1.5"),
            default_salary_basis=SalaryBasis.WORKING_26_DAYS,
            payroll_start_day=1,
            weekly_off_rules=[],
        )
    return EmployeePayrollContext(
        employee=employee,
        business=business,
        attendance_records=attendance_records or [],
        holidays=holidays or [],
    )


PERIOD_JAN = PayrollPeriod.from_year_month(2026, 1, 1)  # Jan 1–31

# Monday=SUNDAY off rule for clarity-free tests
SUNDAY_OFF = [WeeklyOffRule(weekday=Weekday.SUNDAY, week_of_month=None)]


# ── Tests: AttendanceStatus → PayDayType ───────────────────────────────────────


@pytest.mark.asyncio
async def test__present_day_is_paid():
    biz_id = uuid4()
    emp = make_employee(biz_id)
    att = make_attendance(emp, date(2026, 1, 5), AttendanceStatus.PRESENT)  # Monday
    ctx = make_context(emp, [att])
    day_map = DayClassifier.classify_period(PERIOD_JAN, ctx, SUNDAY_OFF)

    assert day_map[date(2026, 1, 5)].day_type == PayDayType.PAID
    assert day_map[date(2026, 1, 5)].regular_hours == Decimal("8")


@pytest.mark.asyncio
async def test__paid_leave_is_paid():
    biz_id = uuid4()
    emp = make_employee(biz_id)
    att = make_attendance(emp, date(2026, 1, 5), AttendanceStatus.PAID_LEAVE)
    ctx = make_context(emp, [att])
    day_map = DayClassifier.classify_period(PERIOD_JAN, ctx, SUNDAY_OFF)

    assert day_map[date(2026, 1, 5)].day_type == PayDayType.PAID
    assert day_map[date(2026, 1, 5)].regular_hours == Decimal("8")


@pytest.mark.asyncio
async def test__unpaid_leave_is_lop():
    biz_id = uuid4()
    emp = make_employee(biz_id)
    att = make_attendance(emp, date(2026, 1, 5), AttendanceStatus.UNPAID_LEAVE)
    ctx = make_context(emp, [att])
    day_map = DayClassifier.classify_period(PERIOD_JAN, ctx, SUNDAY_OFF)

    assert day_map[date(2026, 1, 5)].day_type == PayDayType.LOP
    assert day_map[date(2026, 1, 5)].regular_hours == Decimal("0")


@pytest.mark.asyncio
async def test__half_day_is_half_paid_half_lop():
    biz_id = uuid4()
    emp = make_employee(biz_id)
    att = make_attendance(emp, date(2026, 1, 5), AttendanceStatus.HALF_DAY)
    ctx = make_context(emp, [att])
    day_map = DayClassifier.classify_period(PERIOD_JAN, ctx, SUNDAY_OFF)

    assert day_map[date(2026, 1, 5)].day_type == PayDayType.HALF_PAID_HALF_LOP
    assert day_map[date(2026, 1, 5)].regular_hours == Decimal("4")


# ── Tests: no-attendance fallback rules ───────────────────────────────────────


@pytest.mark.asyncio
async def test__no_attendance_on_working_day_is_lop():
    biz_id = uuid4()
    emp = make_employee(biz_id)
    ctx = make_context(emp, [])  # no attendance records
    day_map = DayClassifier.classify_period(PERIOD_JAN, ctx, SUNDAY_OFF)

    # Jan 5, 2026 is a Monday — working day, no attendance → LOP
    assert day_map[date(2026, 1, 5)].day_type == PayDayType.LOP


@pytest.mark.asyncio
async def test__no_attendance_on_weekly_off_is_paid():
    biz_id = uuid4()
    emp = make_employee(biz_id)
    ctx = make_context(emp, [])
    day_map = DayClassifier.classify_period(PERIOD_JAN, ctx, SUNDAY_OFF)

    # Jan 4, 2026 is a Sunday → weekly off, no attendance → PAID
    assert day_map[date(2026, 1, 4)].day_type == PayDayType.PAID
    assert day_map[date(2026, 1, 4)].is_weekly_off is True


@pytest.mark.asyncio
async def test__no_attendance_on_holiday_is_paid():
    biz_id = uuid4()
    emp = make_employee(biz_id)
    holiday = Holiday.create(
        business_id=biz_id,
        date_=date(2026, 1, 1),
        name="New Year",
    )
    ctx = make_context(emp, [], [holiday])
    day_map = DayClassifier.classify_period(PERIOD_JAN, ctx, SUNDAY_OFF)

    assert day_map[date(2026, 1, 1)].day_type == PayDayType.PAID
    assert day_map[date(2026, 1, 1)].is_holiday is True


# ── Tests: overtime hours propagation ─────────────────────────────────────────


@pytest.mark.asyncio
async def test__overtime_hours_are_captured():
    biz_id = uuid4()
    emp = make_employee(biz_id)
    att = make_attendance(
        emp, date(2026, 1, 5), AttendanceStatus.PRESENT, overtime_hours=Decimal("2")
    )
    ctx = make_context(emp, [att])
    day_map = DayClassifier.classify_period(PERIOD_JAN, ctx, SUNDAY_OFF)

    assert day_map[date(2026, 1, 5)].overtime_hours == Decimal("2")


# ── Tests: PayrollPeriod.from_year_month ──────────────────────────────────────


def test__period_start_day_1_spans_full_month():
    period = PayrollPeriod.from_year_month(2026, 1, 1)
    assert period.start_date == date(2026, 1, 1)
    assert period.end_date == date(2026, 1, 31)


def test__period_start_day_15_spans_mid_month_to_mid_next():
    period = PayrollPeriod.from_year_month(2026, 1, 15)
    assert period.start_date == date(2026, 1, 15)
    assert period.end_date == date(2026, 2, 14)


def test__period_start_day_1_february_non_leap():
    period = PayrollPeriod.from_year_month(2026, 2, 1)
    assert period.start_date == date(2026, 2, 1)
    assert period.end_date == date(2026, 2, 28)


def test__period_start_day_15_december_wraps_year():
    period = PayrollPeriod.from_year_month(2026, 12, 15)
    assert period.start_date == date(2026, 12, 15)
    assert period.end_date == date(2027, 1, 14)
