import hmac
import json
import hashlib

import httpx
from sqlmodel import select

from intentbid.app.db.models import EventOutbox, VendorWebhook
from intentbid.app.services.webhook_service import dispatch_outbox


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


def _submit_offer(client, api_key, rfo_id, price_amount=99.0):
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


def test_register_webhook(client, session):
    api_key, vendor_id, _ = _create_vendor_and_rfo(client)

    response = client.post(
        "/v1/vendors/webhooks",
        json={"url": "https://example.com/webhook"},
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["webhook_id"]
    assert payload["secret"]

    webhook = session.get(VendorWebhook, payload["webhook_id"])
    assert webhook is not None
    assert webhook.vendor_id == vendor_id
    assert webhook.url == "https://example.com/webhook"


def test_outbox_dispatch_delivers_signed_payload(client, session):
    api_key, vendor_id, rfo_id = _create_vendor_and_rfo(client)

    webhook_response = client.post(
        "/v1/vendors/webhooks",
        json={"url": "https://example.com/webhook"},
        headers={"X-API-Key": api_key},
    )
    webhook_payload = webhook_response.json()

    offer_id = _submit_offer(client, api_key, rfo_id)

    event = session.exec(
        select(EventOutbox).where(EventOutbox.vendor_id == vendor_id)
    ).first()
    assert event is not None

    def handler(request):
        raw = request.content.decode("utf-8")
        signature = request.headers.get("X-IntentBid-Signature")
        expected = hmac.new(
            webhook_payload["secret"].encode("utf-8"),
            raw.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assert signature == expected
        payload = json.loads(raw)
        assert payload["event_type"] == "offer.created"
        assert payload["data"]["offer_id"] == offer_id
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    dispatch_outbox(session, client)

    session.refresh(event)
    assert event.status == "delivered"
