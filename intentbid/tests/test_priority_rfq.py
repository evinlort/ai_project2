from intentbid.app.db.models import BuyerSubscription, PlanLimit


def test_priority_rfq_limit_enforced(client, session):
    buyer = client.post("/v1/buyers/register", json={"name": "Buyer"}).json()

    plan = PlanLimit(
        plan_code="buyer-pro",
        max_offers_per_month=0,
        max_rfos_per_month=10,
        max_awards_per_month=5,
        max_priority_rfos_per_month=1,
    )
    session.add(plan)
    session.commit()

    subscription = BuyerSubscription(buyer_id=buyer["buyer_id"], plan_code="buyer-pro", status="active")
    session.add(subscription)
    session.commit()

    payload = {
        "category": "GPU",
        "constraints": {"budget_max": 120000, "priority_rfq": True},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
        "line_items": [{"mpn": "H100-SXM5-80GB", "quantity": 1}],
    }

    first = client.post("/v1/rfo", json=payload, headers={"X-Buyer-API-Key": buyer["api_key"]})
    assert first.status_code == 200

    second = client.post("/v1/rfo", json=payload, headers={"X-Buyer-API-Key": buyer["api_key"]})
    assert second.status_code == 429
