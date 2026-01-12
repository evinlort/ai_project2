from intentbid.app.db.models import Offer, RFO


def _create_vendor_and_rfo(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    vendor_payload = vendor_response.json()

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)

    return vendor_payload["api_key"], vendor_payload["vendor_id"], rfo_response.json()["rfo_id"]


def test_submit_offer_creates_offer(client, session):
    api_key, vendor_id, rfo_id = _create_vendor_and_rfo(client)
    payload = {
        "rfo_id": rfo_id,
        "price_amount": 109.99,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "ABC"},
    }

    response = client.post(
        "/v1/offers",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 200

    offer_id = response.json()["offer_id"]
    offer = session.get(Offer, offer_id)
    assert offer is not None
    assert offer.vendor_id == vendor_id
    assert offer.rfo_id == rfo_id


def test_submit_offer_invalid_rfo_returns_404(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    payload = {
        "rfo_id": 999,
        "price_amount": 109.99,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "ABC"},
    }

    response = client.post(
        "/v1/offers",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 404


def test_submit_offer_closed_rfo_returns_400(client, session):
    api_key, _, rfo_id = _create_vendor_and_rfo(client)
    rfo = session.get(RFO, rfo_id)
    rfo.status = "CLOSED"
    session.add(rfo)
    session.commit()

    payload = {
        "rfo_id": rfo_id,
        "price_amount": 109.99,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "ABC"},
    }

    response = client.post(
        "/v1/offers",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 400
