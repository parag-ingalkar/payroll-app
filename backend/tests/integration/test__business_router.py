import pytest


@pytest.mark.asyncio
async def test__create_business(api_client, business_defaults):
    resp = await api_client.post(
        "/businesses",
        json={
            "name": business_defaults["name"],
            "default_wage_type": business_defaults["default_wage_type"].value,
            "default_working_hours_per_day": "8.0",
            "default_overtime_multiplier": "1.5",
            "payroll_start_day": 1,
            "weekly_off_rules": [],
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test__get_business(api_client, business_defaults):
    # create a business first
    create_resp = await api_client.post(
        "/businesses",
        json={
            "name": business_defaults["name"],
            "default_wage_type": business_defaults["default_wage_type"].value,
            "default_working_hours_per_day": "8.0",
            "default_overtime_multiplier": "1.5",
            "payroll_start_day": 1,
            "weekly_off_rules": [],
        },
    )
    assert create_resp.status_code == 201
    created_business = create_resp.json()

    # now get the business
    get_resp = await api_client.get(f"/businesses/{created_business['id']}")
    assert get_resp.status_code == 200
    fetched_business = get_resp.json()

    assert fetched_business["id"] == created_business["id"]
    assert fetched_business["name"] == business_defaults["name"]


@pytest.mark.asyncio
async def test__list_businesses(api_client, business_defaults):
    # create a business first
    create_resp = await api_client.post(
        "/businesses",
        json={
            "name": business_defaults["name"],
            "default_wage_type": business_defaults["default_wage_type"].value,
            "default_working_hours_per_day": "8.0",
            "default_overtime_multiplier": "1.5",
            "payroll_start_day": 1,
            "weekly_off_rules": [],
        },
    )
    assert create_resp.status_code == 201
    created_business = create_resp.json()

    # now list businesses
    list_resp = await api_client.get("/businesses")
    assert list_resp.status_code == 200
    businesses = list_resp.json()

    assert any(b["id"] == created_business["id"] for b in businesses)


@pytest.mark.asyncio
async def test__get_weekly_off_rules(api_client, business_defaults):
    # create a business first
    create_resp = await api_client.post(
        "/businesses",
        json={
            "name": business_defaults["name"],
            "default_wage_type": business_defaults["default_wage_type"].value,
            "default_working_hours_per_day": "8.0",
            "default_overtime_multiplier": "1.5",
            "payroll_start_day": 1,
            "weekly_off_rules": [
                {"weekday": "sunday"},
                {"weekday": "saturday", "week_of_month": 2},
            ],
        },
    )
    assert create_resp.status_code == 201
    created_business = create_resp.json()

    # now get weekly off rules
    get_rules_resp = await api_client.get(
        f"/businesses/{created_business['id']}/weekly-off-rules"
    )
    assert get_rules_resp.status_code == 200
    rules = get_rules_resp.json()

    assert len(rules) == 2
    assert any(
        rule["weekday"] == "sunday" and rule["week_of_month"] is None for rule in rules
    )
    assert any(
        rule["weekday"] == "saturday" and rule["week_of_month"] == 2 for rule in rules
    )


@pytest.mark.asyncio
async def test__replace_weekly_off_rules(api_client, business_defaults):
    # create a business first
    create_resp = await api_client.post(
        "/businesses",
        json={
            "name": business_defaults["name"],
            "default_wage_type": business_defaults["default_wage_type"].value,
            "default_working_hours_per_day": "8.0",
            "default_overtime_multiplier": "1.5",
            "payroll_start_day": 1,
            "weekly_off_rules": [
                {"weekday": "sunday"},
                {"weekday": "monday", "week_of_month": 1},
            ],
        },
    )
    assert create_resp.status_code == 201
    created_business = create_resp.json()

    # replace weekly off rules
    replace_rules_resp = await api_client.put(
        f"/businesses/{created_business['id']}/weekly-off-rules",
        json=[
            {"weekday": "thursday"},
            {"weekday": "saturday", "week_of_month": 2},
        ],
    )
    assert replace_rules_resp.status_code == 200

    # now get weekly off rules again to verify replacement
    get_rules_resp = await api_client.get(
        f"/businesses/{created_business['id']}/weekly-off-rules"
    )
    assert get_rules_resp.status_code == 200
    rules = get_rules_resp.json()

    assert len(rules) == 2
    assert any(
        rule["weekday"] == "thursday" and rule["week_of_month"] is None
        for rule in rules
    )
    assert any(
        rule["weekday"] == "saturday" and rule["week_of_month"] == 2 for rule in rules
    )


@pytest.mark.asyncio
async def test__update_business(api_client, business_defaults):
    # create a business first
    create_resp = await api_client.post(
        "/businesses",
        json={
            "name": business_defaults["name"],
            "default_wage_type": business_defaults["default_wage_type"].value,
            "default_working_hours_per_day": "8.0",
            "default_overtime_multiplier": "1.5",
            "payroll_start_day": 1,
            "weekly_off_rules": [],
        },
    )
    assert create_resp.status_code == 201
    created_business = create_resp.json()

    # update the business
    update_resp = await api_client.patch(
        f"/businesses/{created_business['id']}",
        json={
            "name": "Updated Business Name",
            "default_wage_type": business_defaults["default_wage_type"].value,
            "default_working_hours_per_day": "9.0",
            "default_overtime_multiplier": "2.0",
            "payroll_start_day": 1,
        },
    )
    assert update_resp.status_code == 200
    updated_business = update_resp.json()

    assert updated_business["id"] == created_business["id"]
    assert updated_business["name"] == "Updated Business Name"
    assert updated_business["default_working_hours_per_day"] == "9.0"
    assert updated_business["default_overtime_multiplier"] == "2.0"


@pytest.mark.asyncio
async def test__delete_business(api_client, business_defaults):
    # create a business first
    create_resp = await api_client.post(
        "/businesses",
        json={
            "name": business_defaults["name"],
            "default_wage_type": business_defaults["default_wage_type"].value,
            "default_working_hours_per_day": "8.0",
            "default_overtime_multiplier": "1.5",
            "payroll_start_day": 1,
            "weekly_off_rules": [],
        },
    )
    assert create_resp.status_code == 201
    created_business = create_resp.json()

    # delete the business
    delete_resp = await api_client.delete(f"/businesses/{created_business['id']}")
    assert delete_resp.status_code == 204

    # now try to get the deleted business, should return 404
    get_resp = await api_client.get(f"/businesses/{created_business['id']}")
    assert get_resp.status_code == 404
