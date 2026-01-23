from intentbid.app.db.models import PlanLimit, Subscription, UsageEvent


def test_dashboard_offers_shows_plan_usage(client, session):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]
    vendor_id = vendor_response.json()["vendor_id"]

    plan = PlanLimit(plan_code="vendor-pro", max_offers_per_month=5)
    session.add(plan)
    session.commit()

    subscription = Subscription(vendor_id=vendor_id, plan_code="vendor-pro", status="active")
    session.add(subscription)
    session.commit()

    session.add(UsageEvent(vendor_id=vendor_id, event_type="offer.created"))
    session.add(UsageEvent(vendor_id=vendor_id, event_type="offer.created"))
    session.commit()

    response = client.get(f"/dashboard/offers?api_key={api_key}")

    assert response.status_code == 200
    assert "Plan usage" in response.text
    assert "2 / 5" in response.text
