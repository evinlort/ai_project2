from datetime import datetime, timedelta, timezone

from intentbid.app.db.models import RFO


def test_rfo_persists_explicit_request_fields(session):
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    rfo = RFO(
        category="sneakers",
        constraints={"budget_max": 120},
        preferences={"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
        title="Wholesale sneakers",
        summary="Bulk request for premium runners",
        budget_max=150.0,
        currency="USD",
        delivery_deadline_days=5,
        quantity=100,
        location="Berlin",
        expires_at=expires_at,
    )

    session.add(rfo)
    session.commit()
    session.refresh(rfo)

    assert rfo.title == "Wholesale sneakers"
    assert rfo.summary == "Bulk request for premium runners"
    assert rfo.budget_max == 150.0
    assert rfo.currency == "USD"
    assert rfo.delivery_deadline_days == 5
    assert rfo.quantity == 100
    assert rfo.location == "Berlin"
    assert rfo.expires_at == expires_at
