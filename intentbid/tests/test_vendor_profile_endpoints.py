def test_vendor_profile_get_put(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    payload = {
        "categories": ["sneakers", "bags"],
        "regions": ["EU", "US"],
        "lead_time_days": 5,
        "min_order_value": 250.0,
    }

    put_response = client.put(
        "/v1/vendors/me/profile",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert put_response.status_code == 200
    put_data = put_response.json()
    assert put_data["categories"] == payload["categories"]
    assert put_data["regions"] == payload["regions"]
    assert put_data["lead_time_days"] == 5
    assert put_data["min_order_value"] == 250.0

    get_response = client.get(
        "/v1/vendors/me/profile", headers={"X-API-Key": api_key}
    )

    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data == put_data
