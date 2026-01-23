from intentbid.app.db.models import RFO


def _register_vendor(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    payload = vendor_response.json()
    return payload["api_key"], payload["vendor_id"]


def _register_buyer(client):
    buyer_response = client.post("/v1/buyers/register", json={"name": "Buyer"})
    return buyer_response.json()


def _create_hardware_rfo(client, buyer_key):
    payload = {
        "category": "GPU",
        "constraints": {"budget_max": 200000, "delivery_deadline_days": 7},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
        "line_items": [{"mpn": "H100-SXM5-80GB", "quantity": 2}],
    }
    response = client.post(
        "/v1/rfo",
        json=payload,
        headers={"X-Buyer-API-Key": buyer_key},
    )
    return response.json()["rfo_id"]


def _submit_offer(client, api_key, rfo_id, price_amount):
    payload = {
        "rfo_id": rfo_id,
        "price_amount": price_amount,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "ABC"},
    }
    response = client.post("/v1/offers", json=payload, headers={"X-API-Key": api_key})
    return response.json()["offer_id"]


def test_recommendation_returns_top_offer(client):
    api_key, _ = _register_vendor(client)
    buyer = _register_buyer(client)
    rfo_id = _create_hardware_rfo(client, buyer["api_key"])

    best_offer = _submit_offer(client, api_key, rfo_id, 90000.0)
    _submit_offer(client, api_key, rfo_id, 110000.0)

    response = client.get(
        f"/v1/rfo/{rfo_id}/recommendation",
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["offer_id"] == best_offer
    assert data["score"] > 0


def test_auto_award_requires_opt_in_and_buyer(client, session):
    api_key, _ = _register_vendor(client)
    buyer = _register_buyer(client)
    rfo_id = _create_hardware_rfo(client, buyer["api_key"])

    offer_id = _submit_offer(client, api_key, rfo_id, 90000.0)

    missing_buyer = client.post(f"/v1/rfo/{rfo_id}/auto_award", json={"opt_in": True})
    assert missing_buyer.status_code == 401

    not_opted = client.post(
        f"/v1/rfo/{rfo_id}/auto_award",
        json={"opt_in": False},
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )
    assert not_opted.status_code == 400

    ok = client.post(
        f"/v1/rfo/{rfo_id}/auto_award",
        json={"opt_in": True, "reason": "auto"},
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )
    assert ok.status_code == 200
    payload = ok.json()
    assert payload["offer_id"] == offer_id
    assert payload["status"] == "AWARDED"

    rfo = session.get(RFO, rfo_id)
    assert rfo.status == "AWARDED"
