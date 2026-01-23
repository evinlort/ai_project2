from sqlmodel import select

from intentbid.app.db.models import AuditLog


def _create_buyer(client, name):
    return client.post("/v1/buyers/register", json={"name": name}).json()


def _create_hardware_rfo(client, buyer_key):
    payload = {
        "category": "GPU",
        "constraints": {"budget_max": 120000, "delivery_deadline_days": 5},
        "preferences": {"w_price": 0.5, "w_delivery": 0.3, "w_warranty": 0.2},
    }
    response = client.post(
        "/v1/rfo",
        json=payload,
        headers={"X-Buyer-API-Key": buyer_key},
    )
    return response.json()["rfo_id"]


def test_hardware_rfo_close_requires_buyer(client):
    buyer = _create_buyer(client, "Buyer")
    other = _create_buyer(client, "Other")
    rfo_id = _create_hardware_rfo(client, buyer["api_key"])

    missing = client.post(f"/v1/rfo/{rfo_id}/close")
    assert missing.status_code == 401

    forbidden = client.post(
        f"/v1/rfo/{rfo_id}/close",
        headers={"X-Buyer-API-Key": other["api_key"]},
    )
    assert forbidden.status_code == 403

    ok = client.post(
        f"/v1/rfo/{rfo_id}/close",
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )
    assert ok.status_code == 200


def test_hardware_rfo_award_requires_owner(client):
    buyer = _create_buyer(client, "Buyer")
    other = _create_buyer(client, "Other")
    rfo_id = _create_hardware_rfo(client, buyer["api_key"])

    close_response = client.post(
        f"/v1/rfo/{rfo_id}/close",
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )
    assert close_response.status_code == 200

    missing = client.post(f"/v1/rfo/{rfo_id}/award")
    assert missing.status_code == 401

    forbidden = client.post(
        f"/v1/rfo/{rfo_id}/award",
        headers={"X-Buyer-API-Key": other["api_key"]},
    )
    assert forbidden.status_code == 403

    ok = client.post(
        f"/v1/rfo/{rfo_id}/award",
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )
    assert ok.status_code == 200


def test_hardware_scoring_update_requires_buyer(client):
    buyer = _create_buyer(client, "Buyer")
    other = _create_buyer(client, "Other")
    rfo_id = _create_hardware_rfo(client, buyer["api_key"])

    missing = client.post(
        f"/v1/rfo/{rfo_id}/scoring",
        json={"weights": {"w_price": 0.7}},
    )
    assert missing.status_code == 401

    forbidden = client.post(
        f"/v1/rfo/{rfo_id}/scoring",
        json={"weights": {"w_price": 0.7}},
        headers={"X-Buyer-API-Key": other["api_key"]},
    )
    assert forbidden.status_code == 403

    ok = client.post(
        f"/v1/rfo/{rfo_id}/scoring",
        json={"weights": {"w_price": 0.7}},
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )
    assert ok.status_code == 200


def test_audit_log_records_buyer_id_and_reason(client, session):
    buyer = _create_buyer(client, "Buyer")
    rfo_id = _create_hardware_rfo(client, buyer["api_key"])

    response = client.post(
        f"/v1/rfo/{rfo_id}/close",
        json={"reason": "buyer_done"},
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )
    assert response.status_code == 200

    audit = session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "rfo",
            AuditLog.entity_id == rfo_id,
            AuditLog.action == "close",
        )
    ).first()
    assert audit is not None
    assert audit.metadata_["reason"] == "buyer_done"
    assert audit.metadata_["buyer_id"] == buyer["buyer_id"]
