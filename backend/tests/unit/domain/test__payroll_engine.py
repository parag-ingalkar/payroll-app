# tests/unit/domain/test__payroll_engine.py
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4


from app.business.domain.entities import Business, WageType
from app.business.domain.value_objects import SalaryBasis
from app.employees.domain.entities import Employee
from app.payroll.domain.day_classifier import EmployeePayrollContext
from app.payroll.domain.engine import PayrollCalculationEngine
from app.payroll.domain.value_objects import (
    DayPayInfo,
    PayDayMap,
    PayDayType,
    PayrollPeriod,
)

# ── Helpers ────────────────────────────────────────────────────────────────────


def make_business(
    salary_basis: SalaryBasis = SalaryBasis.WORKING_26_DAYS,
) -> Business:
    return Business.create(
        owner_id="owner-123",
        name="Test Business",
        default_wage_type=WageType.MONTHLY,
        default_working_hours_per_day=Decimal("8"),
        default_overtime_multiplier=Decimal("1.5"),
        default_salary_basis=salary_basis,
        payroll_start_day=1,
        weekly_off_rules=[],
    )


def make_employee(
    wage_type: WageType = WageType.MONTHLY,
    wage_rate: Decimal = Decimal("52000"),
    hours_per_day: Decimal = Decimal("8"),
    overtime_multiplier: Decimal = Decimal("1.5"),
) -> Employee:
    return Employee.create(
        id=uuid4(),
        business_id=uuid4(),
        name="Test Employee",
        designation="Engineer",
        wage_type=wage_type,
        salary_basis=SalaryBasis.WORKING_26_DAYS,
        wage_rate=wage_rate,
        working_hours_per_day=hours_per_day,
        overtime_multiplier=overtime_multiplier,
    )


def make_context(employee: Employee) -> EmployeePayrollContext:
    """Minimal context — no attendance, no holidays. Business is always valid."""
    return EmployeePayrollContext(
        employee=employee,
        business=make_business(),
        attendance_records=[],
        holidays=[],
    )


def build_full_paid_day_map(
    period: PayrollPeriod,
    hours_per_day: Decimal = Decimal("8"),
) -> PayDayMap:
    day_map: PayDayMap = {}
    current = period.start_date
    while current <= period.end_date:
        day_map[current] = DayPayInfo(
            date=current,
            day_type=PayDayType.PAID,
            regular_hours=hours_per_day,
            overtime_hours=Decimal("0"),
            is_weekly_off=False,
            is_holiday=False,
        )
        current += timedelta(days=1)
    return day_map


def build_day_map_with_lop(
    period: PayrollPeriod,
    lop_dates: list[date],
    hours_per_day: Decimal = Decimal("8"),
) -> PayDayMap:
    day_map: PayDayMap = {}
    current = period.start_date
    while current <= period.end_date:
        is_lop = current in lop_dates
        day_map[current] = DayPayInfo(
            date=current,
            day_type=PayDayType.LOP if is_lop else PayDayType.PAID,
            regular_hours=Decimal("0") if is_lop else hours_per_day,
            overtime_hours=Decimal("0"),
            is_weekly_off=False,
            is_holiday=False,
        )
        current += timedelta(days=1)
    return day_map


ENGINE = PayrollCalculationEngine()
PERIOD = PayrollPeriod.from_year_month(2026, 1, 1)  # Jan 1–31, 31 days
PERIOD_RUN_ID = uuid4()


# ── Monthly / CALENDAR_DAYS ────────────────────────────────────────────────────


def test__monthly_calendar_days_full_attendance_gross_equals_wage():
    emp = make_employee(WageType.MONTHLY, Decimal("31000"))
    day_map = build_full_paid_day_map(PERIOD)
    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.CALENDAR_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    # No LOP → base_pay = wage_rate - 0 = 31000
    assert result.gross_pay == Decimal("31000")
    assert result.lop_days == Decimal("0")
    assert result.basis_days == 31


def test__monthly_calendar_days_with_2_lop_deducts_correctly():
    emp = make_employee(WageType.MONTHLY, Decimal("31000"))
    lop_dates = [date(2026, 1, 5), date(2026, 1, 6)]
    day_map = build_day_map_with_lop(PERIOD, lop_dates)
    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.CALENDAR_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    per_day = Decimal("31000") / Decimal("31")
    expected = Decimal("31000") - per_day * Decimal("2")
    assert result.gross_pay == expected
    assert result.lop_days == Decimal("2")


# ── Monthly / FIXED_30_DAYS ───────────────────────────────────────────────────


def test__monthly_fixed_30_days_basis_is_30():
    emp = make_employee(WageType.MONTHLY, Decimal("30000"))
    day_map = build_full_paid_day_map(PERIOD)
    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.FIXED_30_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    assert result.basis_days == 30
    assert result.gross_pay == Decimal("30000")


def test__monthly_fixed_30_days_with_lop():
    emp = make_employee(WageType.MONTHLY, Decimal("30000"))
    day_map = build_day_map_with_lop(PERIOD, [date(2026, 1, 10)])
    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.FIXED_30_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    per_day = Decimal("30000") / Decimal("30")
    assert result.gross_pay == Decimal("30000") - per_day


# ── Monthly / WORKING_26_DAYS ─────────────────────────────────────────────────


def test__monthly_working_26_days_basis_is_26():
    emp = make_employee(WageType.MONTHLY, Decimal("26000"))
    day_map = build_full_paid_day_map(PERIOD)
    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.WORKING_26_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    assert result.basis_days == 26
    assert result.gross_pay == Decimal("26000")


# ── Daily wage ────────────────────────────────────────────────────────────────


def test__daily_wage_pays_per_paid_day():
    emp = make_employee(WageType.DAILY, Decimal("1000"))
    # Build a map with 20 paid days and 11 LOP
    lop_dates = [date(2026, 1, i) for i in range(21, 32)]
    day_map = build_day_map_with_lop(PERIOD, lop_dates)
    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.CALENDAR_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    assert result.paid_days == Decimal("20")
    assert result.base_pay == Decimal("20000")


def test__daily_wage_full_month_paid():
    emp = make_employee(WageType.DAILY, Decimal("500"))
    day_map = build_full_paid_day_map(PERIOD)
    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.CALENDAR_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    assert result.base_pay == Decimal("500") * Decimal("31")


# ── Hourly wage ───────────────────────────────────────────────────────────────


def test__hourly_wage_pays_per_regular_hours():
    emp = make_employee(WageType.HOURLY, Decimal("100"), hours_per_day=Decimal("8"))
    day_map = build_full_paid_day_map(PERIOD)  # 31 days × 8h = 248h
    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.CALENDAR_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    assert result.base_pay == Decimal("100") * Decimal("248")


# ── Overtime ──────────────────────────────────────────────────────────────────


def test__overtime_is_added_to_gross():
    emp = make_employee(
        WageType.HOURLY, Decimal("100"), overtime_multiplier=Decimal("1.5")
    )
    # 20 regular days, 2h overtime each day
    day_map: PayDayMap = {}
    current = PERIOD.start_date
    while current <= PERIOD.end_date:
        day_map[current] = DayPayInfo(
            date=current,
            day_type=PayDayType.PAID,
            regular_hours=Decimal("8"),
            overtime_hours=Decimal("2"),
            is_weekly_off=False,
            is_holiday=False,
        )
        current += timedelta(days=1)

    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.CALENDAR_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    total_ot_hours = Decimal("2") * Decimal("31")
    expected_ot_pay = Decimal("100") * Decimal("1.5") * total_ot_hours
    assert result.overtime_pay == expected_ot_pay
    assert result.gross_pay == result.base_pay + expected_ot_pay


def test__monthly_overtime_adds_on_top_of_full_salary():
    emp = make_employee(
        WageType.MONTHLY,
        Decimal("31000"),
        hours_per_day=Decimal("8"),
        overtime_multiplier=Decimal("2"),
    )
    # One day of 3h overtime on Jan 15
    day_map: PayDayMap = {}
    current = PERIOD.start_date
    while current <= PERIOD.end_date:
        ot = Decimal("3") if current == date(2026, 1, 15) else Decimal("0")
        day_map[current] = DayPayInfo(
            date=current,
            day_type=PayDayType.PAID,
            regular_hours=Decimal("8"),
            overtime_hours=ot,
            is_weekly_off=False,
            is_holiday=False,
        )
        current += timedelta(days=1)

    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.CALENDAR_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    per_day = Decimal("31000") / Decimal("31")
    per_hour = per_day / Decimal("8")
    expected_ot = per_hour * Decimal("2") * Decimal("3")
    assert result.overtime_pay == expected_ot
    assert result.gross_pay == Decimal("31000") + expected_ot


# ── Half-day ──────────────────────────────────────────────────────────────────


def test__half_day_contributes_half_paid_half_lop():
    emp = make_employee(WageType.MONTHLY, Decimal("30000"))
    day_map: PayDayMap = {}
    current = PERIOD.start_date
    while current <= PERIOD.end_date:
        if current == date(2026, 1, 10):
            day_map[current] = DayPayInfo(
                date=current,
                day_type=PayDayType.HALF_PAID_HALF_LOP,
                regular_hours=Decimal("4"),
                overtime_hours=Decimal("0"),
                is_weekly_off=False,
                is_holiday=False,
            )
        else:
            day_map[current] = DayPayInfo(
                date=current,
                day_type=PayDayType.PAID,
                regular_hours=Decimal("8"),
                overtime_hours=Decimal("0"),
                is_weekly_off=False,
                is_holiday=False,
            )
        current += timedelta(days=1)

    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.FIXED_30_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    # (correct — 30 full paid days + 0.5 from the half-day)
    assert result.paid_days == Decimal("30.5")
    assert result.lop_days == Decimal("0.5")

    # Also verify the pay — deduction is on LOP side, not paid side
    # base_pay = 30000 - (30000/30 * 0.5) = 30000 - 500 = 29500
    assert result.base_pay == Decimal("29500.0")
    # (correct — 30 full paid days + 0.5 from the half-day)
    assert result.paid_days == Decimal("30.5")
    assert result.lop_days == Decimal("0.5")

    # Also verify the pay — deduction is on LOP side, not paid side
    # base_pay = 30000 - (30000/30 * 0.5) = 30000 - 500 = 29500
    assert result.base_pay == Decimal("29500.0")


# ── Line item output fields ────────────────────────────────────────────────────


def test__line_item_has_correct_employee_fields():
    emp = make_employee(WageType.MONTHLY, Decimal("40000"))
    day_map = build_full_paid_day_map(PERIOD)
    result = ENGINE.calculate_employee(
        period=PERIOD,
        context=make_context(emp),
        day_pay_map=day_map,
        salary_basis=SalaryBasis.WORKING_26_DAYS,
        payroll_run_id=PERIOD_RUN_ID,
    )
    assert result.employee_id == emp.id
    assert result.employee_name == emp.name
    assert result.wage_type == WageType.MONTHLY
    assert result.wage_rate == Decimal("40000")
    assert result.payroll_run_id == PERIOD_RUN_ID
    assert result.id is not None
