def test_vendor_offers_list_returns_request_summary(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    vendor_payload = vendor_response.json()

    other_vendor_response = client.post("/v1/vendors/register", json={"name": "Other"})
    other_vendor_payload = other_vendor_response.json()

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
        "title": "Bulk sneakers",
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    rfo_id = rfo_response.json()["rfo_id"]

    offer_payload = {
        "rfo_id": rfo_id,
        "price_amount": 99.0,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "B"},
    }
    offer_response = client.post(
        "/v1/offers", json=offer_payload, headers={"X-API-Key": vendor_payload["api_key"]}
    )
    offer_id = offer_response.json()["offer_id"]

    client.post(
        "/v1/offers", json=offer_payload, headers={"X-API-Key": other_vendor_payload["api_key"]}
    )

    response = client.get(
        "/v1/vendors/me/offers", headers={"X-API-Key": vendor_payload["api_key"]}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["offer_id"] == offer_id
    assert data["items"][0]["request"]["id"] == rfo_id
    assert data["items"][0]["request"]["category"] == "sneakers"
    assert data["items"][0]["request"]["title"] == "Bulk sneakers"
    assert data["items"][0]["status"] == "submitted"
    assert data["items"][0]["is_awarded"] is False
