from sqlmodel import select

from intentbid.app.db.models import AuditLog


def _create_buyer(client, name):
    return client.post("/v1/buyers/register", json={"name": name}).json()


def _create_buyer_rfo(client, buyer_key):
    payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
        "title": "Initial request",
    }
    response = client.post(
        "/v1/rfo",
        json=payload,
        headers={"X-Buyer-API-Key": buyer_key},
    )
    return response.json()["rfo_id"]


def test_buyer_updates_open_rfo_and_logs_audit(client, session):
    buyer = _create_buyer(client, "Buyer One")
    rfo_id = _create_buyer_rfo(client, buyer["api_key"])

    patch_payload = {
        "title": "Updated request",
        "budget_max": 140.0,
        "delivery_deadline_days": 7,
    }
    response = client.patch(
        f"/v1/rfo/{rfo_id}",
        json=patch_payload,
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Updated request"
    assert data["budget_max"] == 140.0
    assert data["delivery_deadline_days"] == 7
    assert data["constraints"]["budget_max"] == 140.0
    assert data["constraints"]["delivery_deadline_days"] == 7

    audit = session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "rfo",
            AuditLog.entity_id == rfo_id,
            AuditLog.action == "update",
        )
    ).first()
    assert audit is not None


def test_buyer_update_requires_open_status(client):
    buyer = _create_buyer(client, "Buyer One")
    rfo_id = _create_buyer_rfo(client, buyer["api_key"])

    client.post(f"/v1/rfo/{rfo_id}/close")

    response = client.patch(
        f"/v1/rfo/{rfo_id}",
        json={"title": "Closed update"},
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )

    assert response.status_code == 400


def test_buyer_update_enforces_ownership(client):
    buyer_one = _create_buyer(client, "Buyer One")
    buyer_two = _create_buyer(client, "Buyer Two")
    rfo_id = _create_buyer_rfo(client, buyer_one["api_key"])

    response = client.patch(
        f"/v1/rfo/{rfo_id}",
        json={"title": "Unauthorized update"},
        headers={"X-Buyer-API-Key": buyer_two["api_key"]},
    )

    assert response.status_code == 403
