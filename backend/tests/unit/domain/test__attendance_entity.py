# tests/unit/domain/test__attendance_entity.py
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.attendance.domain.entities import Attendance, AttendanceStatus
from app.attendance.domain.exceptions import OvertimeNotAllowedError

BUSINESS_ID = UUID("12345678-1234-5678-1234-567812345678")
EMPLOYEE_ID = UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")
TEST_DATE = date(2026, 6, 1)


def _make_attendance(**overrides) -> Attendance:
    return Attendance.create(
        id=overrides.get("id", uuid4()),
        business_id=overrides.get("business_id", BUSINESS_ID),
        employee_id=overrides.get("employee_id", EMPLOYEE_ID),
        date=overrides.get("date", TEST_DATE),
        status=overrides.get("status", AttendanceStatus.PRESENT),
        overtime_hours=overrides.get("overtime_hours", Decimal("0")),
    )


def test__create_attendance_present_no_overtime():
    att = _make_attendance()
    assert att.status == AttendanceStatus.PRESENT
    assert att.overtime_hours == Decimal("0")
    assert att.business_id == BUSINESS_ID
    assert att.employee_id == EMPLOYEE_ID
    assert att.date == TEST_DATE


def test__create_attendance_present_with_overtime():
    att = _make_attendance(overtime_hours=Decimal("2.5"))
    assert att.status == AttendanceStatus.PRESENT
    assert att.overtime_hours == Decimal("2.5")


def test__create_attendance_paid_leave_no_overtime():
    att = _make_attendance(status=AttendanceStatus.PAID_LEAVE)
    assert att.status == AttendanceStatus.PAID_LEAVE
    assert att.overtime_hours == Decimal("0")


def test__create_attendance_unpaid_leave_no_overtime():
    att = _make_attendance(status=AttendanceStatus.UNPAID_LEAVE)
    assert att.status == AttendanceStatus.UNPAID_LEAVE
    assert att.overtime_hours == Decimal("0")


def test__create_attendance_half_day_no_overtime():
    att = _make_attendance(status=AttendanceStatus.HALF_DAY)
    assert att.status == AttendanceStatus.HALF_DAY
    assert att.overtime_hours == Decimal("0")


def test__create_attendance_paid_leave_with_overtime_raises_error():
    with pytest.raises(OvertimeNotAllowedError):
        _make_attendance(
            status=AttendanceStatus.PAID_LEAVE, overtime_hours=Decimal("2.0")
        )


def test__create_attendance_unpaid_leave_with_overtime_raises_error():
    with pytest.raises(OvertimeNotAllowedError):
        _make_attendance(
            status=AttendanceStatus.UNPAID_LEAVE, overtime_hours=Decimal("1.0")
        )


def test__create_attendance_half_day_with_overtime_raises_error():
    with pytest.raises(OvertimeNotAllowedError):
        _make_attendance(
            status=AttendanceStatus.HALF_DAY, overtime_hours=Decimal("3.0")
        )


def test__update_status_from_present_to_paid_leave_clears_overtime():
    att = _make_attendance(
        status=AttendanceStatus.PRESENT, overtime_hours=Decimal("2.0")
    )
    att.update_status(AttendanceStatus.PAID_LEAVE)
    assert att.status == AttendanceStatus.PAID_LEAVE
    assert att.overtime_hours == Decimal("0")


def test__update_status_from_present_to_half_day_clears_overtime():
    att = _make_attendance(
        status=AttendanceStatus.PRESENT, overtime_hours=Decimal("1.5")
    )
    att.update_status(AttendanceStatus.HALF_DAY)
    assert att.status == AttendanceStatus.HALF_DAY
    assert att.overtime_hours == Decimal("0")


def test__update_status_from_present_to_unpaid_leave_clears_overtime():
    att = _make_attendance(
        status=AttendanceStatus.PRESENT, overtime_hours=Decimal("1.0")
    )
    att.update_status(AttendanceStatus.UNPAID_LEAVE)
    assert att.status == AttendanceStatus.UNPAID_LEAVE
    assert att.overtime_hours == Decimal("0")


def test__update_status_to_present_does_not_clear_overtime():
    att = _make_attendance(
        status=AttendanceStatus.PRESENT, overtime_hours=Decimal("1.5")
    )
    att.update_status(AttendanceStatus.PRESENT)
    assert att.status == AttendanceStatus.PRESENT
    assert att.overtime_hours == Decimal("1.5")


def test__update_status_from_non_present_to_present_keeps_zero_overtime():
    att = _make_attendance(status=AttendanceStatus.PAID_LEAVE)
    att.update_status(AttendanceStatus.PRESENT)
    assert att.status == AttendanceStatus.PRESENT
    assert att.overtime_hours == Decimal("0")


def test__set_overtime_on_present_status_succeeds():
    att = _make_attendance(status=AttendanceStatus.PRESENT)
    att.set_overtime(Decimal("3.5"))
    assert att.overtime_hours == Decimal("3.5")


def test__set_overtime_to_zero_on_present_is_allowed():
    att = _make_attendance(
        status=AttendanceStatus.PRESENT, overtime_hours=Decimal("2.0")
    )
    att.set_overtime(Decimal("0"))
    assert att.overtime_hours == Decimal("0")


def test__set_overtime_on_paid_leave_raises_error():
    att = _make_attendance(status=AttendanceStatus.PAID_LEAVE)
    with pytest.raises(OvertimeNotAllowedError):
        att.set_overtime(Decimal("2.0"))


def test__set_overtime_on_unpaid_leave_raises_error():
    att = _make_attendance(status=AttendanceStatus.UNPAID_LEAVE)
    with pytest.raises(OvertimeNotAllowedError):
        att.set_overtime(Decimal("2.0"))


def test__set_overtime_on_half_day_raises_error():
    att = _make_attendance(status=AttendanceStatus.HALF_DAY)
    with pytest.raises(OvertimeNotAllowedError):
        att.set_overtime(Decimal("2.0"))
