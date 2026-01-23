from sqlmodel import select

from intentbid.app.db.models import Offer, RFO


def test_idempotency_key_reuses_rfo_response(client, session):
    payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }

    headers = {"Idempotency-Key": "rfo-key-1"}
    first = client.post("/v1/rfo", json=payload, headers=headers)
    assert first.status_code == 200
    rfo_id = first.json()["rfo_id"]

    second = client.post("/v1/rfo", json=payload, headers=headers)
    assert second.status_code == 200
    assert second.json()["rfo_id"] == rfo_id

    count = session.exec(select(RFO)).all()
    assert len(count) == 1


def test_idempotency_key_reuses_offer_response(client, session):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
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
        "metadata": {"sku": "ABC"},
    }

    headers = {"X-API-Key": api_key, "Idempotency-Key": "offer-key-1"}
    first = client.post("/v1/offers", json=offer_payload, headers=headers)
    assert first.status_code == 200
    offer_id = first.json()["offer_id"]

    second = client.post("/v1/offers", json=offer_payload, headers=headers)
    assert second.status_code == 200
    assert second.json()["offer_id"] == offer_id

    offers = session.exec(select(Offer)).all()
    assert len(offers) == 1
