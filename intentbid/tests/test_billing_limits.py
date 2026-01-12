from sqlmodel import select

from intentbid.app.db.models import PlanLimit, Subscription, UsageEvent


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


def _offer_payload(rfo_id, price_amount):
    return {
        "rfo_id": rfo_id,
        "price_amount": price_amount,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": f"{price_amount}"},
    }


def test_offer_limits_enforced_by_plan(client, session):
    api_key, vendor_id, rfo_id = _create_vendor_and_rfo(client)

    plan = PlanLimit(plan_code="basic", max_offers_per_month=1)
    session.add(plan)
    session.commit()

    subscription = Subscription(vendor_id=vendor_id, plan_code="basic", status="active")
    session.add(subscription)
    session.commit()

    first = client.post("/v1/offers", json=_offer_payload(rfo_id, 90.0), headers={"X-API-Key": api_key})
    assert first.status_code == 200

    second = client.post("/v1/offers", json=_offer_payload(rfo_id, 95.0), headers={"X-API-Key": api_key})
    assert second.status_code == 429
    assert "plan limit" in second.json()["detail"].lower()

    events = session.exec(
        select(UsageEvent).where(UsageEvent.vendor_id == vendor_id)
    ).all()
    assert len(events) == 1
