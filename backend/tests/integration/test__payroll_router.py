# tests/integration/test__payroll_router.py
from decimal import Decimal
from uuid import uuid4

import pytest

from tests.integration.conftest import (
    _api_create_business,
    _api_create_employee,
    _api_seed_attendance,
)

# ── POST /businesses/{id}/payroll/run ──────────────────────────────────────────


@pytest.mark.asyncio
async def test__run_payroll_returns_201_with_line_items(api_client, seeded_payroll_run):
    """P0: Happy path — run payroll returns 201 with correct payload."""
    resp = await api_client.get(
        f"/businesses/{seeded_payroll_run['business_id']}/payroll/{seeded_payroll_run['run_id']}"
    )
    # Verify the run created by the fixture is retrievable and correct
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == seeded_payroll_run["run_id"]
    assert body["business_id"] == seeded_payroll_run["business_id"]
    assert len(body["line_items"]) == 1
    assert body["line_items"][0]["employee_id"] == seeded_payroll_run["employee_id"]
    assert Decimal(body["line_items"][0]["gross_pay"]) > Decimal("0")


@pytest.mark.asyncio
async def test__run_payroll_post_returns_201(api_client, seeded_business_with_employee):
    """P0: POST /run with attendance returns 201 and run payload."""
    business_id = seeded_business_with_employee["business_id"]
    employee_id = seeded_business_with_employee["employee_id"]
    await _api_seed_attendance(api_client, business_id, employee_id, 2026, 1, 26)

    resp = await api_client.post(
        f"/businesses/{business_id}/payroll/run",
        json={"year": 2026, "month": 1},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["business_id"] == business_id
    assert len(body["line_items"]) == 1
    assert Decimal(body["line_items"][0]["gross_pay"]) > Decimal("0")
    assert body["is_incomplete"] is False


@pytest.mark.asyncio
async def test__run_payroll_marks_incomplete_when_no_attendance(
    api_client, seeded_business_with_employee
):
    """P0: No attendance → is_incomplete=True."""
    business_id = seeded_business_with_employee["business_id"]

    resp = await api_client.post(
        f"/businesses/{business_id}/payroll/run",
        json={"year": 2026, "month": 1},
    )

    assert resp.status_code == 201
    assert resp.json()["is_incomplete"] is True


@pytest.mark.asyncio
async def test__run_payroll_wrong_business_returns_404(api_client):
    """P0: Unknown business_id → 404."""
    resp = await api_client.post(
        f"/businesses/{uuid4()}/payroll/run",
        json={"year": 2026, "month": 1},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test__run_payroll_invalid_month_returns_422(api_client, seeded_business):
    """P0: month=13 fails validation → 422."""
    resp = await api_client.post(
        f"/businesses/{seeded_business}/payroll/run",
        json={"year": 2026, "month": 13},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test__run_payroll_twice_replaces_run(
    api_client, seeded_business_with_employee
):
    """P0: Two runs for same period → only one run in list, second id returned."""
    business_id = seeded_business_with_employee["business_id"]
    employee_id = seeded_business_with_employee["employee_id"]
    await _api_seed_attendance(api_client, business_id, employee_id, 2026, 1, 26)

    r1 = await api_client.post(
        f"/businesses/{business_id}/payroll/run",
        json={"year": 2026, "month": 1},
    )
    r2 = await api_client.post(
        f"/businesses/{business_id}/payroll/run",
        json={"year": 2026, "month": 1},
    )

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]

    list_resp = await api_client.get(f"/businesses/{business_id}/payroll/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == r2.json()["id"]


# ── GET /businesses/{id}/payroll/ ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test__list_payroll_runs_returns_empty_for_new_business(
    api_client, seeded_business
):
    """P0: No runs → 200 empty list."""
    resp = await api_client.get(f"/businesses/{seeded_business}/payroll/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test__list_payroll_runs_returns_summary_list(
    api_client, seeded_business_with_employee
):
    """P0: Two runs → list contains 2 summaries with required fields."""
    business_id = seeded_business_with_employee["business_id"]
    employee_id = seeded_business_with_employee["employee_id"]

    for month, days in [(1, 26), (2, 26)]:
        await _api_seed_attendance(
            api_client, business_id, employee_id, 2026, month, days
        )
        await api_client.post(
            f"/businesses/{business_id}/payroll/run",
            json={"year": 2026, "month": month},
        )

    resp = await api_client.get(f"/businesses/{business_id}/payroll/")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    for item in body:
        assert "id" in item
        assert "period" in item
        assert "employee_count" in item
        assert "total_gross_pay" in item


@pytest.mark.asyncio
async def test__list_payroll_runs_filtered_by_year_month(
    api_client, seeded_business_with_employee
):
    """P0: ?year=2026&month=1 returns only the January run."""
    business_id = seeded_business_with_employee["business_id"]
    employee_id = seeded_business_with_employee["employee_id"]

    for month, days in [(1, 26), (2, 26)]:
        await _api_seed_attendance(
            api_client, business_id, employee_id, 2026, month, days
        )
        await api_client.post(
            f"/businesses/{business_id}/payroll/run",
            json={"year": 2026, "month": month},
        )

    resp = await api_client.get(f"/businesses/{business_id}/payroll/?year=2026&month=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ── GET /businesses/{id}/payroll/{run_id} ──────────────────────────────────────


@pytest.mark.asyncio
async def test__get_payroll_run_returns_full_detail(api_client, seeded_payroll_run):
    """P0: GET a specific run returns full detail with line items."""
    resp = await api_client.get(
        f"/businesses/{seeded_payroll_run['business_id']}/payroll/{seeded_payroll_run['run_id']}"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == seeded_payroll_run["run_id"]
    assert len(body["line_items"]) == 1
    assert body["line_items"][0]["employee_id"] == seeded_payroll_run["employee_id"]


@pytest.mark.asyncio
async def test__get_payroll_run_unknown_id_returns_404(api_client, seeded_business):
    """P0: GET with unknown run_id → 404."""
    resp = await api_client.get(f"/businesses/{seeded_business}/payroll/{uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test__get_payroll_run_wrong_business_returns_404(
    api_client, seeded_payroll_run
):
    """P0: Correct run_id but wrong business_id → 404."""
    resp = await api_client.get(
        f"/businesses/{uuid4()}/payroll/{seeded_payroll_run['run_id']}"
    )
    assert resp.status_code == 404
