
def _create_vendor_offer(client, rfo_id):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

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
    response = client.post(
        "/v1/offers", json=offer_payload, headers={"X-API-Key": api_key}
    )
    return response.json()["offer_id"]


def test_buyer_offers_list_requires_buyer_key(client):
    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    rfo_id = rfo_response.json()["rfo_id"]

    response = client.get(f"/v1/rfo/{rfo_id}/offers")

    assert response.status_code == 401


def test_buyer_offers_list_enforces_ownership(client):
    buyer_one = client.post("/v1/buyers/register", json={"name": "Buyer One"}).json()
    buyer_two = client.post("/v1/buyers/register", json={"name": "Buyer Two"}).json()

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post(
        "/v1/rfo",
        json=rfo_payload,
        headers={"X-Buyer-API-Key": buyer_one["api_key"]},
    )
    rfo_id = rfo_response.json()["rfo_id"]
    offer_id = _create_vendor_offer(client, rfo_id)

    response = client.get(
        f"/v1/rfo/{rfo_id}/offers",
        headers={"X-Buyer-API-Key": buyer_two["api_key"]},
    )

    assert response.status_code == 403

    ok_response = client.get(
        f"/v1/rfo/{rfo_id}/offers",
        headers={"X-Buyer-API-Key": buyer_one["api_key"]},
    )

    assert ok_response.status_code == 200
    data = ok_response.json()
    assert data["rfo_id"] == rfo_id
    assert data["offers"][0]["id"] == offer_id
