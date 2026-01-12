import time

from intentbid.app.core.config import settings


def _create_vendor_and_rfo(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    vendor_payload = vendor_response.json()

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    return vendor_payload["api_key"], rfo_response.json()["rfo_id"]


def _offer_payload(rfo_id, price_amount=99.0, delivery_eta_days=2, warranty_months=12):
    return {
        "rfo_id": rfo_id,
        "price_amount": price_amount,
        "currency": "USD",
        "delivery_eta_days": delivery_eta_days,
        "warranty_months": warranty_months,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "ABC"},
    }


def test_offer_limit_per_vendor_rfo(client, monkeypatch):
    monkeypatch.setattr(settings, "max_offers_per_vendor_rfo", 2)
    monkeypatch.setattr(settings, "offer_cooldown_seconds", 0)

    api_key, rfo_id = _create_vendor_and_rfo(client)
    headers = {"X-API-Key": api_key}

    first = client.post("/v1/offers", json=_offer_payload(rfo_id, price_amount=90.0), headers=headers)
    assert first.status_code == 200

    second = client.post("/v1/offers", json=_offer_payload(rfo_id, price_amount=95.0), headers=headers)
    assert second.status_code == 200

    third = client.post("/v1/offers", json=_offer_payload(rfo_id, price_amount=97.0), headers=headers)
    assert third.status_code == 429
    assert "limit" in third.json()["detail"].lower()


def test_offer_cooldown_enforced(client, monkeypatch):
    monkeypatch.setattr(settings, "max_offers_per_vendor_rfo", 10)
    monkeypatch.setattr(settings, "offer_cooldown_seconds", 1)

    api_key, rfo_id = _create_vendor_and_rfo(client)
    headers = {"X-API-Key": api_key}

    first = client.post("/v1/offers", json=_offer_payload(rfo_id, price_amount=90.0), headers=headers)
    assert first.status_code == 200

    second = client.post("/v1/offers", json=_offer_payload(rfo_id, price_amount=95.0), headers=headers)
    assert second.status_code == 429

    time.sleep(1.1)
    third = client.post("/v1/offers", json=_offer_payload(rfo_id, price_amount=99.0), headers=headers)
    assert third.status_code == 200


def test_offer_validation_rejects_invalid_ranges(client):
    api_key, rfo_id = _create_vendor_and_rfo(client)
    headers = {"X-API-Key": api_key}

    bad_price = client.post(
        "/v1/offers",
        json=_offer_payload(rfo_id, price_amount=-1),
        headers=headers,
    )
    assert bad_price.status_code == 400
