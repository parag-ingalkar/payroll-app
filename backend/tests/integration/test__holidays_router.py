# tests/integration/test__holidays_router.py
from uuid import UUID

import pytest

BASE_URL = "/businesses"


@pytest.mark.asyncio
async def test__create_holiday_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": "2026-01-01", "name": "New Year's Day"},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["date"] == "2026-01-01"
    assert data["name"] == "New Year's Day"
    # basic shape
    assert "id" in data
    UUID(data["id"])  # valid UUID


@pytest.mark.asyncio
async def test__create_duplicate_holiday_returns_409(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    body = {"date": "2026-01-01", "name": "New Year's Day"}

    # First create succeeds
    resp1 = await api_client.post(f"{BASE_URL}/{business_id}/holidays", json=body)
    assert resp1.status_code == 201

    # Second create for same business + date → HolidayAlreadyExistsError → 409
    resp2 = await api_client.post(f"{BASE_URL}/{business_id}/holidays", json=body)
    assert resp2.status_code == 409
    detail = resp2.json()["detail"]
    assert detail["code"] == "holiday_already_exists"
    assert "date" in detail.get("fields", [])


@pytest.mark.asyncio
async def test__list_holidays_returns_sorted_results(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    # Create two holidays on different dates
    await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": "2026-01-26", "name": "Republic Day"},
    )
    await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": "2026-01-01", "name": "New Year's Day"},
    )

    # List without filters; use case sorts by date
    resp = await api_client.get(f"{BASE_URL}/{business_id}/holidays")
    assert resp.status_code == 200
    data = resp.json()
    assert [h["date"] for h in data] == ["2026-01-01", "2026-01-26"]


@pytest.mark.asyncio
async def test__get_holiday_by_date_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()

    await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": "2026-01-01", "name": "New Year's Day"},
    )

    resp = await api_client.get(
        f"{BASE_URL}/{business_id}/holidays/2026-01-01",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == "2026-01-01"
    assert data["name"] == "New Year's Day"


@pytest.mark.asyncio
async def test__get_holiday_by_date_not_found_returns_404(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    resp = await api_client.get(
        f"{BASE_URL}/{business_id}/holidays/2026-02-01",
    )
    assert resp.status_code == 404
    # Router raises HTTPException("Holiday not found") when business exists but holiday doesn’t
    assert resp.json()["detail"]["message"] == "Holiday not found."


@pytest.mark.asyncio
async def test__update_holiday_name_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()

    create_resp = await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": "2026-01-01", "name": "New Year's Day"},
    )
    assert create_resp.status_code == 201

    patch_resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/holidays/2026-01-01",
        json={"name": "New Year's Celebration"},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["name"] == "New Year's Celebration"
    assert data["date"] == "2026-01-01"


@pytest.mark.asyncio
async def test__update_holiday_clear_name_with_null(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": "2026-01-01", "name": "New Year's Day"},
    )

    patch_resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/holidays/2026-01-01",
        json={"name": None},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["name"] is None


@pytest.mark.asyncio
async def test__update_holiday_without_fields_returns_400(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": "2026-01-01", "name": "New Year's Day"},
    )

    patch_resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/holidays/2026-01-01",
        json={},
    )
    assert patch_resp.status_code == 400
    assert patch_resp.json()["detail"]["message"] == "No fields to update."


@pytest.mark.asyncio
async def test__update_holiday_not_found_returns_404(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    patch_resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/holidays/2026-02-01",
        json={"name": "Some Holiday"},
    )
    assert patch_resp.status_code == 404
    # HolidayNotFoundError -> router-level 404 "Holiday not found"
    assert patch_resp.json()["detail"]["message"] == "Holiday not found."


@pytest.mark.asyncio
async def test__delete_holiday_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()

    await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": "2026-01-01", "name": "New Year's Day"},
    )

    delete_resp = await api_client.delete(
        f"{BASE_URL}/{business_id}/holidays/2026-01-01",
    )
    assert delete_resp.status_code == 204

    get_resp = await api_client.get(
        f"{BASE_URL}/{business_id}/holidays/2026-01-01",
    )
    assert get_resp.status_code == 404
    assert get_resp.json()["detail"]["message"] == "Holiday not found."


@pytest.mark.asyncio
async def test__holiday_routes_respect_business_ownership(
    api_client, create_business_via_api
):
    """
    Ownership E2E:
    - Create a business for the current user.
    - Create a holiday for that business.
    - Try to access holidays for a different business id: should return business_not_found.
    """
    business_id = await create_business_via_api()
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    # Create holiday for the real business
    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/holidays",
        json={"date": "2026-01-01", "name": "New Year's Day"},
    )
    assert resp.status_code == 201

    # Try to list holidays for a different business id
    list_resp = await api_client.get(
        f"{BASE_URL}/{other_business_id}/holidays",
    )
    assert list_resp.status_code == 404
    detail = list_resp.json()["detail"]
    # This comes from BusinessNotFoundError handler
    assert detail["code"] == "business_not_found"
    assert detail["message"] == "Business not found."


@pytest.mark.asyncio
async def test__create_holiday_wrong_business_returns_404(
    api_client, create_business_via_api
):
    """Attempt to create holiday for a business that doesn't exist or doesn't belong to the user."""
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    resp = await api_client.post(
        f"{BASE_URL}/{other_business_id}/holidays",
        json={"date": "2026-01-01", "name": "New Year's Day"},
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["code"] == "business_not_found"


@pytest.mark.asyncio
async def test__get_holiday_by_date_wrong_business_returns_404(
    api_client, create_business_via_api
):
    """Attempt to get a holiday from a business that doesn't exist or doesn't belong to the user."""
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    resp = await api_client.get(
        f"{BASE_URL}/{other_business_id}/holidays/2026-01-01",
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["code"] == "business_not_found"


@pytest.mark.asyncio
async def test__update_holiday_wrong_business_returns_404(
    api_client, create_business_via_api
):
    """Attempt to update a holiday for a business that doesn't exist or doesn't belong to the user."""
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    resp = await api_client.patch(
        f"{BASE_URL}/{other_business_id}/holidays/2026-01-01",
        json={"name": "Updated Name"},
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["code"] == "business_not_found"


@pytest.mark.asyncio
async def test__delete_holiday_wrong_business_returns_404(
    api_client, create_business_via_api
):
    """Attempt to delete a holiday from a business that doesn't exist or doesn't belong to the user."""
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    resp = await api_client.delete(
        f"{BASE_URL}/{other_business_id}/holidays/2026-01-01",
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["code"] == "business_not_found"
