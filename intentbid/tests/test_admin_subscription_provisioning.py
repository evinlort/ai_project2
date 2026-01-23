from intentbid.app.core.config import settings
from intentbid.app.db.models import BuyerSubscription, Subscription


def test_admin_can_provision_buyer_subscription(client, session, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "admin-secret")
    buyer = client.post("/v1/buyers/register", json={"name": "Buyer"}).json()

    response = client.post(
        f"/v1/admin/buyers/{buyer['buyer_id']}/subscription",
        json={"plan_code": "buyer-pro", "status": "active"},
        headers={"X-Admin-API-Key": "admin-secret"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["plan_code"] == "buyer-pro"

    stored = session.get(BuyerSubscription, data["subscription_id"])
    assert stored is not None
    assert stored.buyer_id == buyer["buyer_id"]


def test_admin_can_provision_vendor_subscription(client, session, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "admin-secret")
    vendor = client.post("/v1/vendors/register", json={"name": "Vendor"}).json()

    response = client.post(
        f"/v1/admin/vendors/{vendor['vendor_id']}/subscription",
        json={"plan_code": "vendor-pro", "status": "active"},
        headers={"X-Admin-API-Key": "admin-secret"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["plan_code"] == "vendor-pro"

    stored = session.get(Subscription, data["subscription_id"])
    assert stored is not None
    assert stored.vendor_id == vendor["vendor_id"]
