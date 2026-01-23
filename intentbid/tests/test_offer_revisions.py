from datetime import datetime, timedelta, timezone

from intentbid.app.core.config import settings
from sqlmodel import select

from intentbid.app.db.models import Offer, OfferRevision


def _register_vendor_and_rfo(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    return api_key, rfo_response.json()["rfo_id"]


def _submit_offer(client, api_key, rfo_id, valid_until=None):
    payload = {
        "rfo_id": rfo_id,
        "price_amount": 99.0,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "ABC"},
    }
    if valid_until is not None:
        payload["valid_until"] = valid_until
    response = client.post("/v1/offers", json=payload, headers={"X-API-Key": api_key})
    return response.json()["offer_id"]


def test_offer_update_creates_revision_and_increments_version(client, session):
    api_key, rfo_id = _register_vendor_and_rfo(client)
    offer_id = _submit_offer(
        client,
        api_key,
        rfo_id,
        valid_until=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    )

    update = client.patch(
        f"/v1/offers/{offer_id}",
        json={"price_amount": 95.0, "delivery_eta_days": 1},
        headers={"X-API-Key": api_key},
    )
    assert update.status_code == 200
    assert update.json()["offer_version"] == 2

    offer = session.get(Offer, offer_id)
    assert offer.offer_version == 2
    assert offer.price_amount == 95.0

    revision = session.exec(
        select(OfferRevision).where(OfferRevision.offer_id == offer_id)
    ).first()
    assert revision is not None
    assert revision.offer_version == 1


def test_offer_update_rejects_expired_valid_until(client):
    api_key, rfo_id = _register_vendor_and_rfo(client)
    offer_id = _submit_offer(
        client,
        api_key,
        rfo_id,
        valid_until=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
    )

    update = client.patch(
        f"/v1/offers/{offer_id}",
        json={"price_amount": 95.0},
        headers={"X-API-Key": api_key},
    )

    assert update.status_code == 400


def test_offer_update_respects_cooldown(client, monkeypatch):
    monkeypatch.setattr(settings, "offer_cooldown_seconds", 60)

    api_key, rfo_id = _register_vendor_and_rfo(client)
    offer_id = _submit_offer(
        client,
        api_key,
        rfo_id,
        valid_until=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    )

    first = client.patch(
        f"/v1/offers/{offer_id}",
        json={"price_amount": 95.0},
        headers={"X-API-Key": api_key},
    )
    assert first.status_code == 200

    second = client.patch(
        f"/v1/offers/{offer_id}",
        json={"price_amount": 94.0},
        headers={"X-API-Key": api_key},
    )
    assert second.status_code == 429
