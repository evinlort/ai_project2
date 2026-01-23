from sqlmodel import select

from intentbid.app.db.models import EventOutbox


def test_rfo_quote_deadline_persists(client):
    payload = {
        "category": "GPU",
        "constraints": {"budget_max": 50000, "delivery_deadline_days": 5},
        "preferences": {"w_price": 0.5, "w_delivery": 0.3, "w_warranty": 0.2},
        "line_items": [{"mpn": "H100-SXM5-80GB", "quantity": 1}],
        "quote_deadline_hours": 2,
    }

    response = client.post("/v1/rfo", json=payload)
    assert response.status_code == 200

    rfo_id = response.json()["rfo_id"]
    detail = client.get(f"/v1/rfo/{rfo_id}")
    assert detail.status_code == 200
    assert detail.json()["quote_deadline_hours"] == 2


def test_rfo_created_event_includes_quote_deadline(client, session):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    vendor_id = vendor_response.json()["vendor_id"]

    payload = {
        "category": "GPU",
        "constraints": {"budget_max": 50000, "delivery_deadline_days": 5},
        "preferences": {"w_price": 0.5, "w_delivery": 0.3, "w_warranty": 0.2},
        "line_items": [{"mpn": "H100-SXM5-80GB", "quantity": 1}],
        "quote_deadline_hours": 4,
    }
    response = client.post("/v1/rfo", json=payload)
    rfo_id = response.json()["rfo_id"]

    event = session.exec(
        select(EventOutbox).where(
            EventOutbox.vendor_id == vendor_id,
            EventOutbox.event_type == "rfo.created",
        )
    ).first()

    assert event is not None
    assert event.payload["rfo_id"] == rfo_id
    assert event.payload["quote_deadline_hours"] == 4
