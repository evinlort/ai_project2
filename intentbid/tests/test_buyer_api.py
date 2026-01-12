def _create_vendor_and_rfo(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    vendor_payload = vendor_response.json()

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    rfo_id = rfo_response.json()["rfo_id"]
    return vendor_payload["api_key"], rfo_id


def _create_offer(client, api_key, rfo_id, price_amount, delivery_eta_days, warranty_months):
    offer_payload = {
        "rfo_id": rfo_id,
        "price_amount": price_amount,
        "currency": "USD",
        "delivery_eta_days": delivery_eta_days,
        "warranty_months": warranty_months,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": f"{price_amount}"},
    }
    client.post(
        "/v1/offers",
        json=offer_payload,
        headers={"X-API-Key": api_key},
    )
    return rfo_id


def test_register_buyer_and_auth(client):
    response = client.post("/v1/buyers/register", json={"name": "BuyerCo"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["buyer_id"]
    assert payload["api_key"]

    unauthorized = client.get("/v1/buyers/me")
    assert unauthorized.status_code == 401

    authorized = client.get(
        "/v1/buyers/me",
        headers={"X-Buyer-API-Key": payload["api_key"]},
    )
    assert authorized.status_code == 200
    assert authorized.json()["buyer_id"] == payload["buyer_id"]


def test_buyer_ranking_returns_all_offers_sorted(client):
    response = client.post("/v1/buyers/register", json={"name": "BuyerCo"})
    buyer_payload = response.json()

    api_key, rfo_id = _create_vendor_and_rfo(client)
    _create_offer(client, api_key, rfo_id, 100.0, 2, 12)
    _create_offer(client, api_key, rfo_id, 90.0, 1, 6)

    ranking_response = client.get(
        f"/v1/buyers/rfo/{rfo_id}/ranking",
        headers={"X-Buyer-API-Key": buyer_payload["api_key"]},
    )
    assert ranking_response.status_code == 200

    payload = ranking_response.json()
    offers = payload["offers"]
    assert len(offers) == 2
    assert offers[0]["score"] >= offers[1]["score"]
    assert offers[0]["offer"]["rfo_id"] == rfo_id
