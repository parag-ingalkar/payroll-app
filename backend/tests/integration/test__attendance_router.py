# tests/integration/test__attendance_router.py
from uuid import UUID

import pytest

BASE_URL = "/businesses"

# Dates relative to today (2026-06-22):
# past, no holiday by default
PAST_DATE = "2026-06-10"
# used to create a holiday in relevant tests
HOLIDAY_DATE = "2026-06-15"
# in the future
FUTURE_DATE = "2026-12-31"


async def _create_employee(
    api_client, business_id: UUID, name: str = "John Doe"
) -> str:
    """Create an employee via HTTP and return its id."""
    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json={"name": name, "wage_rate": "50000.00"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _mark_attendance(
    api_client,
    business_id: UUID,
    employee_id: str,
    *,
    date: str = PAST_DATE,
    status: str = "present",
    overtime_hours: str | None = None,
) -> dict:
    """Mark attendance via HTTP and return the response body."""
    payload: dict = {"employee_id": employee_id, "date": date, "status": status}
    if overtime_hours is not None:
        payload["overtime_hours"] = overtime_hours
    resp = await api_client.post(f"{BASE_URL}/{business_id}/attendance", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ─── Mark Attendance ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__mark_attendance_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance",
        json={
            "employee_id": employee_id,
            "date": PAST_DATE,
            "status": "present",
            "overtime_hours": "2.5",
        },
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["employee_id"] == employee_id
    assert data["date"] == PAST_DATE
    assert data["status"] == "present"
    assert float(data["overtime_hours"]) == 2.5
    assert "id" in data
    UUID(data["id"])  # valid UUID


@pytest.mark.asyncio
async def test__mark_attendance_paid_leave_no_overtime(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance",
        json={"employee_id": employee_id, "date": PAST_DATE, "status": "paid_leave"},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "paid_leave"
    assert float(data["overtime_hours"]) == 0.0


@pytest.mark.asyncio
async def test__mark_attendance_duplicate_returns_409(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)
    await _mark_attendance(api_client, business_id, employee_id)

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance",
        json={"employee_id": employee_id, "date": PAST_DATE, "status": "paid_leave"},
    )

    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["code"] == "attendance_already_exists"
    assert "employee_id" in detail.get("fields", [])


@pytest.mark.asyncio
async def test__mark_attendance_future_date_returns_400(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance",
        json={"employee_id": employee_id, "date": FUTURE_DATE, "status": "present"},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "attendance_future_date"


@pytest.mark.asyncio
async def test__mark_attendance_on_holiday_returns_409(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    # Create a holiday for that date via HTTP
    holiday_resp = await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": HOLIDAY_DATE, "name": "Test Holiday"},
    )
    assert holiday_resp.status_code == 201

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance",
        json={"employee_id": employee_id, "date": HOLIDAY_DATE, "status": "present"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "attendance_on_holiday"


@pytest.mark.asyncio
async def test__mark_attendance_inactive_employee_returns_400(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    # Deactivate employee via dedicated endpoint
    deactivate_resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/employees/{employee_id}/deactivate",
    )
    assert deactivate_resp.status_code == 204

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance",
        json={"employee_id": employee_id, "date": PAST_DATE, "status": "present"},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "inactive_employee_attendance"


@pytest.mark.asyncio
async def test__mark_attendance_wrong_business_returns_404(
    api_client, create_business_via_api
):
    await create_business_via_api()
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    employee_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    resp = await api_client.post(
        f"{BASE_URL}/{other_business_id}/attendance",
        json={"employee_id": employee_id, "date": PAST_DATE, "status": "present"},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "business_not_found"


# ─── Get Attendance ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__get_attendance_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)
    await _mark_attendance(api_client, business_id, employee_id)

    resp = await api_client.get(
        f"{BASE_URL}/{business_id}/attendance/{employee_id}/{PAST_DATE}"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["employee_id"] == employee_id
    assert data["date"] == PAST_DATE
    assert data["status"] == "present"


@pytest.mark.asyncio
async def test__get_attendance_not_found_returns_404(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    resp = await api_client.get(
        f"{BASE_URL}/{business_id}/attendance/{employee_id}/{PAST_DATE}"
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "attendance_not_found"


@pytest.mark.asyncio
async def test__get_attendance_wrong_business_returns_404(
    api_client, create_business_via_api
):
    await create_business_via_api()
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    employee_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    resp = await api_client.get(
        f"{BASE_URL}/{other_business_id}/attendance/{employee_id}/{PAST_DATE}"
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "business_not_found"


# ─── List Attendance by Date ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__list_attendance_by_date_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)
    await _mark_attendance(api_client, business_id, employee_id)

    resp = await api_client.get(
        f"{BASE_URL}/{business_id}/attendance/by-date?date={PAST_DATE}"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["employee_id"] == employee_id


@pytest.mark.asyncio
async def test__list_attendance_by_date_status_filter(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    emp1_id = await _create_employee(api_client, business_id, name="Alice")
    emp2_id = await _create_employee(api_client, business_id, name="Bob")

    await _mark_attendance(api_client, business_id, emp1_id, status="present")
    await _mark_attendance(api_client, business_id, emp2_id, status="paid_leave")

    resp = await api_client.get(
        f"{BASE_URL}/{business_id}/attendance/by-date?date={PAST_DATE}&status=present"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "present"


@pytest.mark.asyncio
async def test__list_attendance_by_date_returns_empty_list(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    resp = await api_client.get(
        f"{BASE_URL}/{business_id}/attendance/by-date?date={PAST_DATE}"
    )

    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test__list_attendance_by_date_wrong_business_returns_404(
    api_client, create_business_via_api
):
    await create_business_via_api()
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    resp = await api_client.get(
        f"{BASE_URL}/{other_business_id}/attendance/by-date?date={PAST_DATE}"
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "business_not_found"


# ─── List Attendance by Employee ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test__list_attendance_by_employee_happy_path(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    for day in [2, 5, 10]:
        resp = await api_client.post(
            f"{BASE_URL}/{business_id}/attendance",
            json={
                "employee_id": employee_id,
                "date": f"2026-06-{day:02d}",
                "status": "present",
            },
        )
        assert resp.status_code == 201

    resp = await api_client.get(
        f"{BASE_URL}/{business_id}/attendance/by-employee/{employee_id}"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert data[0]["date"] == "2026-06-02"
    assert data[-1]["date"] == "2026-06-10"


@pytest.mark.asyncio
async def test__list_attendance_by_employee_date_range_filter(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    for day in [1, 2, 3, 4, 5]:
        resp = await api_client.post(
            f"{BASE_URL}/{business_id}/attendance",
            json={
                "employee_id": employee_id,
                "date": f"2026-06-{day:02d}",
                "status": "present",
            },
        )
        assert resp.status_code == 201

    resp = await api_client.get(
        f"{BASE_URL}/{business_id}/attendance/by-employee/{employee_id}"
        f"?start_date=2026-06-02&end_date=2026-06-04"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert data[0]["date"] == "2026-06-02"
    assert data[-1]["date"] == "2026-06-04"


@pytest.mark.asyncio
async def test__list_attendance_by_employee_wrong_business_returns_404(
    api_client, create_business_via_api
):
    await create_business_via_api()
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    employee_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    resp = await api_client.get(
        f"{BASE_URL}/{other_business_id}/attendance/by-employee/{employee_id}"
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "business_not_found"


# ─── Update Attendance ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__update_attendance_status(api_client, create_business_via_api):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)
    await _mark_attendance(api_client, business_id, employee_id)

    resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/attendance/{employee_id}/{PAST_DATE}",
        json={"status": "paid_leave"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "paid_leave"
    assert float(data["overtime_hours"]) == 0.0


@pytest.mark.asyncio
async def test__update_attendance_set_overtime(api_client, create_business_via_api):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)
    await _mark_attendance(api_client, business_id, employee_id)

    resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/attendance/{employee_id}/{PAST_DATE}",
        json={"overtime_hours": "3.5"},
    )

    assert resp.status_code == 200
    assert float(resp.json()["overtime_hours"]) == 3.5


@pytest.mark.asyncio
async def test__update_attendance_overtime_on_non_present_returns_400(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)
    await _mark_attendance(api_client, business_id, employee_id, status="paid_leave")

    resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/attendance/{employee_id}/{PAST_DATE}",
        json={"overtime_hours": "2.0"},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "overtime_not_allowed"


@pytest.mark.asyncio
async def test__update_attendance_no_fields_returns_400(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)
    await _mark_attendance(api_client, business_id, employee_id)

    resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/attendance/{employee_id}/{PAST_DATE}",
        json={},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "no_fields_to_update"


@pytest.mark.asyncio
async def test__update_attendance_not_found_returns_404(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/attendance/{employee_id}/{PAST_DATE}",
        json={"status": "paid_leave"},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "attendance_not_found"


@pytest.mark.asyncio
async def test__update_attendance_wrong_business_returns_404(
    api_client, create_business_via_api
):
    await create_business_via_api()
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    employee_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    resp = await api_client.patch(
        f"{BASE_URL}/{other_business_id}/attendance/{employee_id}/{PAST_DATE}",
        json={"status": "paid_leave"},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "business_not_found"


# ─── Delete Attendance ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__delete_attendance_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)
    await _mark_attendance(api_client, business_id, employee_id)

    resp = await api_client.delete(
        f"{BASE_URL}/{business_id}/attendance/{employee_id}/{PAST_DATE}"
    )

    assert resp.status_code == 204

    # Verify the record is gone
    get_resp = await api_client.get(
        f"{BASE_URL}/{business_id}/attendance/{employee_id}/{PAST_DATE}"
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test__delete_attendance_not_found_returns_404(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    resp = await api_client.delete(
        f"{BASE_URL}/{business_id}/attendance/{employee_id}/{PAST_DATE}"
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "attendance_not_found"


@pytest.mark.asyncio
async def test__delete_attendance_wrong_business_returns_404(
    api_client, create_business_via_api
):
    await create_business_via_api()
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    employee_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    resp = await api_client.delete(
        f"{BASE_URL}/{other_business_id}/attendance/{employee_id}/{PAST_DATE}"
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "business_not_found"


# ─── Bulk Mark Attendance ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__bulk_mark_attendance_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()
    emp1_id = await _create_employee(api_client, business_id, name="Alice")
    emp2_id = await _create_employee(api_client, business_id, name="Bob")

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/bulk",
        json={
            "date": PAST_DATE,
            "entries": [
                {"employee_id": emp1_id, "status": "present", "overtime_hours": "1.5"},
                {"employee_id": emp2_id, "status": "paid_leave"},
            ],
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test__bulk_mark_attendance_overwrites_existing(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    # Initial attendance via single mark
    await _mark_attendance(api_client, business_id, employee_id, status="present")

    # Overwrite via bulk
    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/bulk",
        json={
            "date": PAST_DATE,
            "entries": [{"employee_id": employee_id, "status": "paid_leave"}],
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "paid_leave"


@pytest.mark.asyncio
async def test__bulk_mark_attendance_future_date_returns_400(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/bulk",
        json={
            "date": FUTURE_DATE,
            "entries": [{"employee_id": employee_id, "status": "present"}],
        },
    )

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "attendance_future_date"


@pytest.mark.asyncio
async def test__bulk_mark_attendance_holiday_returns_409(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": HOLIDAY_DATE, "name": "Test Holiday"},
    )

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/bulk",
        json={
            "date": HOLIDAY_DATE,
            "entries": [{"employee_id": employee_id, "status": "present"}],
        },
    )

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "attendance_on_holiday"


@pytest.mark.asyncio
async def test__bulk_mark_attendance_empty_entries_returns_422(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/bulk",
        json={"date": PAST_DATE, "entries": []},
    )

    # Pydantic min_length=1 validation error
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test__bulk_mark_attendance_wrong_business_returns_404(
    api_client, create_business_via_api
):
    await create_business_via_api()
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    employee_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    resp = await api_client.post(
        f"{BASE_URL}/{other_business_id}/attendance/bulk",
        json={
            "date": PAST_DATE,
            "entries": [{"employee_id": employee_id, "status": "present"}],
        },
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "business_not_found"


# ─── Mark All Present ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test__mark_all_present_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()
    await _create_employee(api_client, business_id, name="Alice")
    await _create_employee(api_client, business_id, name="Bob")

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/mark-all-present",
        json={"date": PAST_DATE},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(r["status"] == "present" for r in data)
    assert all(float(r["overtime_hours"]) == 0.0 for r in data)


@pytest.mark.asyncio
async def test__mark_all_present_overwrites_existing(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    # First mark as paid_leave
    await _mark_attendance(api_client, business_id, employee_id, status="paid_leave")

    # Then mark all present (should overwrite)
    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/mark-all-present",
        json={"date": PAST_DATE},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "present"


@pytest.mark.asyncio
async def test__mark_all_present_future_date_returns_400(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/mark-all-present",
        json={"date": FUTURE_DATE},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "attendance_future_date"


@pytest.mark.asyncio
async def test__mark_all_present_holiday_returns_409(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": HOLIDAY_DATE, "name": "Test Holiday"},
    )

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/mark-all-present",
        json={"date": HOLIDAY_DATE},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "attendance_on_holiday"


@pytest.mark.asyncio
async def test__mark_all_present_no_employees_returns_empty_list(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/mark-all-present",
        json={"date": PAST_DATE},
    )

    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test__mark_all_present_wrong_business_returns_404(
    api_client, create_business_via_api
):
    await create_business_via_api()
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    resp = await api_client.post(
        f"{BASE_URL}/{other_business_id}/attendance/mark-all-present",
        json={"date": PAST_DATE},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "business_not_found"


# ─── Weekly Off restriction ───────────────────────────────────────────────────
# June 11, 2026 is a Thursday (1st Thursday of June).
# Tests below set Thursday as a weekly off and verify the 409 response.
WEEKLY_OFF_DATE = "2026-06-11"


@pytest.mark.asyncio
async def test__mark_attendance_on_weekly_off_returns_409(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    # Set Thursday as a weekly off day via the business API
    rules_resp = await api_client.put(
        f"{BASE_URL}/{business_id}/weekly-off-rules",
        json=[{"weekday": "thursday", "week_of_month": None}],
    )
    assert rules_resp.status_code == 200

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance",
        json={"employee_id": employee_id, "date": WEEKLY_OFF_DATE, "status": "present"},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "attendance_on_weekly_off"


@pytest.mark.asyncio
async def test__bulk_mark_attendance_on_weekly_off_returns_409(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    employee_id = await _create_employee(api_client, business_id)

    rules_resp = await api_client.put(
        f"{BASE_URL}/{business_id}/weekly-off-rules",
        json=[{"weekday": "thursday", "week_of_month": None}],
    )
    assert rules_resp.status_code == 200

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/bulk",
        json={
            "date": WEEKLY_OFF_DATE,
            "entries": [{"employee_id": employee_id, "status": "present"}],
        },
    )

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "attendance_on_weekly_off"


@pytest.mark.asyncio
async def test__mark_all_present_on_weekly_off_returns_409(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    rules_resp = await api_client.put(
        f"{BASE_URL}/{business_id}/weekly-off-rules",
        json=[{"weekday": "thursday", "week_of_month": None}],
    )
    assert rules_resp.status_code == 200

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/attendance/mark-all-present",
        json={"date": WEEKLY_OFF_DATE},
    )

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "attendance_on_weekly_off"
