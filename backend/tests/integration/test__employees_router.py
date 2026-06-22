# tests/integration/test__employees_router.py
from uuid import UUID

import pytest

BASE_URL = "/businesses"


def _employee_payload(**overrides) -> dict:
    defaults: dict = {
        "name": "John Doe",
        "wage_rate": "50000.00",
    }
    defaults.update(overrides)
    return defaults


@pytest.mark.asyncio
async def test__create_employee_with_explicit_wage_fields(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(
            wage_type="monthly",
            working_hours_per_day="8.0",
            overtime_multiplier="1.5",
        ),
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "John Doe"
    assert data["wage_type"] == "monthly"
    assert data["is_active"] is True
    assert "id" in data
    UUID(data["id"])


@pytest.mark.asyncio
async def test__create_employee_uses_business_defaults(
    api_client, create_business_via_api
):
    """Omitting wage_type, working_hours_per_day, overtime_multiplier should
    fall back to business defaults."""
    business_id = await create_business_via_api()

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(),  # no wage_type, no working_hours_per_day, no overtime_multiplier
    )

    assert resp.status_code == 201
    data = resp.json()
    # business defaults: wage_type=hourly, working_hours_per_day=8.0, overtime_multiplier=1.5
    assert data["wage_type"] == "hourly"
    assert float(data["working_hours_per_day"]) == 8.0
    assert float(data["overtime_multiplier"]) == 1.5


@pytest.mark.asyncio
async def test__create_employee_with_designation(api_client, create_business_via_api):
    business_id = await create_business_via_api()

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(designation="Senior Engineer"),
    )

    assert resp.status_code == 201
    assert resp.json()["designation"] == "Senior Engineer"


@pytest.mark.asyncio
async def test__list_employees_returns_sorted_results(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(name="Zara Ali"),
    )
    await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(name="Alice Sharma"),
    )

    resp = await api_client.get(f"{BASE_URL}/{business_id}/employees")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert [e["name"] for e in data] == ["Alice Sharma", "Zara Ali"]


@pytest.mark.asyncio
async def test__list_employees_filter_by_active(api_client, create_business_via_api):
    business_id = await create_business_via_api()

    await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(name="Active Person"),
    )
    create_resp2 = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(name="Inactive Person"),
    )
    assert create_resp2.status_code == 201
    employee_id2 = create_resp2.json()["id"]

    patch_resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/employees/{employee_id2}",
        json={"is_active": False},
    )
    assert patch_resp.status_code == 200

    active_resp = await api_client.get(
        f"{BASE_URL}/{business_id}/employees?is_active=true"
    )
    assert active_resp.status_code == 200
    assert len(active_resp.json()) == 1
    assert active_resp.json()[0]["name"] == "Active Person"

    inactive_resp = await api_client.get(
        f"{BASE_URL}/{business_id}/employees?is_active=false"
    )
    assert inactive_resp.status_code == 200
    assert len(inactive_resp.json()) == 1
    assert inactive_resp.json()[0]["name"] == "Inactive Person"


@pytest.mark.asyncio
async def test__get_employee_by_id_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()

    create_resp = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(),
    )
    assert create_resp.status_code == 201
    employee_id = create_resp.json()["id"]

    resp = await api_client.get(f"{BASE_URL}/{business_id}/employees/{employee_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == employee_id
    assert data["name"] == "John Doe"


@pytest.mark.asyncio
async def test__get_employee_by_id_not_found_returns_404(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    nonexistent_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    resp = await api_client.get(f"{BASE_URL}/{business_id}/employees/{nonexistent_id}")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "employee_not_found"


@pytest.mark.asyncio
async def test__update_employee_name_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()

    create_resp = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(),
    )
    assert create_resp.status_code == 201
    employee_id = create_resp.json()["id"]

    patch_resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/employees/{employee_id}",
        json={"name": "John D."},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "John D."


@pytest.mark.asyncio
async def test__update_employee_clears_designation(api_client, create_business_via_api):
    business_id = await create_business_via_api()

    create_resp = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(designation="Engineer"),
    )
    assert create_resp.status_code == 201
    employee_id = create_resp.json()["id"]
    assert create_resp.json()["designation"] == "Engineer"

    patch_resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/employees/{employee_id}",
        json={"designation": None},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["designation"] is None


@pytest.mark.asyncio
async def test__update_employee_wage_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()

    create_resp = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(),
    )
    assert create_resp.status_code == 201
    employee_id = create_resp.json()["id"]

    patch_resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/employees/{employee_id}",
        json={"wage_type": "daily", "wage_rate": "2000.00"},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["wage_type"] == "daily"
    assert float(data["wage_rate"]) == 2000.00


@pytest.mark.asyncio
async def test__update_employee_without_fields_returns_400(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()

    create_resp = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(),
    )
    assert create_resp.status_code == 201
    employee_id = create_resp.json()["id"]

    patch_resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/employees/{employee_id}",
        json={},
    )
    assert patch_resp.status_code == 400
    assert patch_resp.json()["detail"]["message"] == "No fields to update."


@pytest.mark.asyncio
async def test__update_employee_not_found_returns_404(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    nonexistent_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    patch_resp = await api_client.patch(
        f"{BASE_URL}/{business_id}/employees/{nonexistent_id}",
        json={"name": "Ghost"},
    )
    assert patch_resp.status_code == 404
    assert patch_resp.json()["detail"]["code"] == "employee_not_found"


@pytest.mark.asyncio
async def test__delete_employee_happy_path(api_client, create_business_via_api):
    business_id = await create_business_via_api()

    create_resp = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(),
    )
    assert create_resp.status_code == 201
    employee_id = create_resp.json()["id"]

    delete_resp = await api_client.delete(
        f"{BASE_URL}/{business_id}/employees/{employee_id}"
    )
    assert delete_resp.status_code == 204

    get_resp = await api_client.get(f"{BASE_URL}/{business_id}/employees/{employee_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test__delete_employee_not_found_returns_404(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    nonexistent_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    delete_resp = await api_client.delete(
        f"{BASE_URL}/{business_id}/employees/{nonexistent_id}"
    )
    assert delete_resp.status_code == 404
    assert delete_resp.json()["detail"]["code"] == "employee_not_found"


@pytest.mark.asyncio
async def test__employee_routes_respect_business_ownership(
    api_client, create_business_via_api
):
    business_id = await create_business_via_api()
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    resp = await api_client.post(
        f"{BASE_URL}/{business_id}/employees",
        json=_employee_payload(),
    )
    assert resp.status_code == 201

    list_resp = await api_client.get(f"{BASE_URL}/{other_business_id}/employees")
    assert list_resp.status_code == 404
    detail = list_resp.json()["detail"]
    assert detail["code"] == "business_not_found"


@pytest.mark.asyncio
async def test__create_employee_wrong_business_returns_404(
    api_client, create_business_via_api
):
    """Attempt to create employee for a business that doesn't exist or doesn't belong to the user."""
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    resp = await api_client.post(
        f"{BASE_URL}/{other_business_id}/employees",
        json=_employee_payload(),
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["code"] == "business_not_found"


@pytest.mark.asyncio
async def test__get_employee_by_id_wrong_business_returns_404(
    api_client, create_business_via_api
):
    """Attempt to get an employee from a business that doesn't exist or doesn't belong to the user."""
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    employee_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    resp = await api_client.get(
        f"{BASE_URL}/{other_business_id}/employees/{employee_id}"
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["code"] == "business_not_found"


@pytest.mark.asyncio
async def test__update_employee_wrong_business_returns_404(
    api_client, create_business_via_api
):
    """Attempt to update an employee for a business that doesn't exist or doesn't belong to the user."""
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    employee_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    resp = await api_client.patch(
        f"{BASE_URL}/{other_business_id}/employees/{employee_id}",
        json={"name": "Updated Name"},
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["code"] == "business_not_found"


@pytest.mark.asyncio
async def test__delete_employee_wrong_business_returns_404(
    api_client, create_business_via_api
):
    """Attempt to delete an employee from a business that doesn't exist or doesn't belong to the user."""
    other_business_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    employee_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    resp = await api_client.delete(
        f"{BASE_URL}/{other_business_id}/employees/{employee_id}"
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["code"] == "business_not_found"
