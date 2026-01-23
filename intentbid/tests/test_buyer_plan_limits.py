from sqlmodel import select

from intentbid.app.db.models import BuyerSubscription, BuyerUsageEvent, PlanLimit


def _register_buyer(client):
    return client.post("/v1/buyers/register", json={"name": "Buyer"}).json()


def _register_vendor(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    payload = vendor_response.json()
    return payload["api_key"], payload["vendor_id"]


def _create_rfo(client, buyer_key):
    payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    return client.post("/v1/rfo", json=payload, headers={"X-Buyer-API-Key": buyer_key})


def _submit_offer(client, api_key, rfo_id):
    payload = {
        "rfo_id": rfo_id,
        "price_amount": 90.0,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "ABC"},
    }
    response = client.post("/v1/offers", json=payload, headers={"X-API-Key": api_key})
    return response.json()["offer_id"]


def test_buyer_rfo_plan_limit_enforced(client, session):
    buyer = _register_buyer(client)

    plan = PlanLimit(plan_code="buyer-free", max_offers_per_month=0, max_rfos_per_month=1, max_awards_per_month=1)
    session.add(plan)
    session.commit()

    subscription = BuyerSubscription(buyer_id=buyer["buyer_id"], plan_code="buyer-free", status="active")
    session.add(subscription)
    session.commit()

    first = _create_rfo(client, buyer["api_key"])
    assert first.status_code == 200

    second = _create_rfo(client, buyer["api_key"])
    assert second.status_code == 429

    events = session.exec(
        select(BuyerUsageEvent).where(BuyerUsageEvent.buyer_id == buyer["buyer_id"])
    ).all()
    assert len(events) == 1


def test_buyer_award_plan_limit_enforced(client, session):
    buyer = _register_buyer(client)
    api_key, _ = _register_vendor(client)

    plan = PlanLimit(plan_code="buyer-pro", max_offers_per_month=0, max_rfos_per_month=10, max_awards_per_month=1)
    session.add(plan)
    session.commit()

    subscription = BuyerSubscription(buyer_id=buyer["buyer_id"], plan_code="buyer-pro", status="active")
    session.add(subscription)
    session.commit()

    first_rfo = _create_rfo(client, buyer["api_key"])
    rfo_id = first_rfo.json()["rfo_id"]
    offer_id = _submit_offer(client, api_key, rfo_id)

    client.post(f"/v1/rfo/{rfo_id}/close", json={})
    award = client.post(
        f"/v1/rfo/{rfo_id}/award",
        json={"offer_id": offer_id},
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )
    assert award.status_code == 200

    second_rfo = _create_rfo(client, buyer["api_key"])
    rfo_id_2 = second_rfo.json()["rfo_id"]
    offer_id_2 = _submit_offer(client, api_key, rfo_id_2)

    client.post(f"/v1/rfo/{rfo_id_2}/close", json={})
    denied = client.post(
        f"/v1/rfo/{rfo_id_2}/award",
        json={"offer_id": offer_id_2},
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )
    assert denied.status_code == 429
