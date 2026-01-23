from datetime import datetime, timedelta, timezone

from intentbid.app.core.config import settings
from intentbid.app.db.models import Vendor


def _register_vendor(client, name="Acme"):
    payload = client.post("/v1/vendors/register", json={"name": name}).json()
    return payload["vendor_id"], payload["api_key"]


def _hardware_rfo(client):
    payload = {
        "category": "GPU",
        "constraints": {"budget_max": 100000, "delivery_deadline_days": 5},
        "preferences": {"w_price": 0.5, "w_delivery": 0.3, "w_warranty": 0.2},
        "line_items": [{"mpn": "H100-SXM5-80GB", "quantity": 2}],
    }
    return client.post("/v1/rfo", json=payload).json()["rfo_id"]


def _admin_headers():
    return {"X-Admin-API-Key": "admin-secret"}


def test_admin_approves_and_suspends_vendor(client, session, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "admin-secret")
    vendor_id, _ = _register_vendor(client)

    approve = client.post(
        f"/v1/admin/vendors/{vendor_id}/approve",
        json={"notes": "verified docs"},
        headers=_admin_headers(),
    )
    assert approve.status_code == 200
    payload = approve.json()
    assert payload["verification_status"] == "VERIFIED"
    assert payload["verification_notes"] == "verified docs"
    assert payload["verified_at"]

    vendor = session.get(Vendor, vendor_id)
    assert vendor.verification_status == "VERIFIED"

    suspend = client.post(
        f"/v1/admin/vendors/{vendor_id}/suspend",
        json={"notes": "issue found"},
        headers=_admin_headers(),
    )
    assert suspend.status_code == 200
    assert suspend.json()["verification_status"] == "SUSPENDED"


def test_admin_updates_vendor_reputation(client, session, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "admin-secret")
    vendor_id, _ = _register_vendor(client)

    response = client.patch(
        f"/v1/admin/vendors/{vendor_id}/reputation",
        json={
            "on_time_delivery_rate": 0.98,
            "dispute_rate": 0.01,
            "verified_distributor": True,
        },
        headers=_admin_headers(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["on_time_delivery_rate"] == 0.98
    assert data["dispute_rate"] == 0.01
    assert data["verified_distributor"] is True


def test_hardware_offer_requires_verified_vendor(client, monkeypatch):
    monkeypatch.setattr(settings, "require_verified_vendors_for_hardware", True)
    monkeypatch.setattr(settings, "admin_api_key", "admin-secret")

    vendor_id, api_key = _register_vendor(client)
    rfo_id = _hardware_rfo(client)

    offer_payload = {
        "rfo_id": rfo_id,
        "unit_price": 90000.0,
        "currency": "USD",
        "lead_time_days": 4,
        "available_qty": 2,
        "condition": "new",
        "warranty_months": 12,
        "return_days": 30,
        "traceability": {
            "authorized_channel": True,
            "invoices_available": True,
            "serials_available": True,
        },
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
    }

    blocked = client.post(
        "/v1/offers",
        json=offer_payload,
        headers={"X-API-Key": api_key},
    )
    assert blocked.status_code == 403

    approve = client.post(
        f"/v1/admin/vendors/{vendor_id}/approve",
        json={"notes": "ok"},
        headers=_admin_headers(),
    )
    assert approve.status_code == 200

    allowed = client.post(
        "/v1/offers",
        json=offer_payload,
        headers={"X-API-Key": api_key},
    )
    assert allowed.status_code == 200
