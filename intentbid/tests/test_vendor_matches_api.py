def test_vendor_matches_filters_by_category_and_region(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    profile_payload = {
        "categories": ["sneakers"],
        "regions": ["EU"],
        "lead_time_days": 5,
        "min_order_value": 200.0,
    }
    client.put(
        "/v1/vendors/me/profile",
        json=profile_payload,
        headers={"X-API-Key": api_key},
    )

    base_payload = {
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }

    match_rfo = client.post(
        "/v1/rfo",
        json={
            **base_payload,
            "category": "sneakers",
            "location": "EU",
        },
    ).json()["rfo_id"]

    client.post(
        "/v1/rfo",
        json={
            **base_payload,
            "category": "bags",
            "location": "EU",
        },
    )
    client.post(
        "/v1/rfo",
        json={
            **base_payload,
            "category": "sneakers",
            "location": "US",
        },
    )

    response = client.get(
        "/v1/vendors/me/matches", headers={"X-API-Key": api_key}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["rfo"]["id"] == match_rfo
    assert "category_match" in data["items"][0]["reasons"]
    assert "region_match" in data["items"][0]["reasons"]
