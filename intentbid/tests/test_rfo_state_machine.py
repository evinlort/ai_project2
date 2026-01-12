from sqlmodel import select

from intentbid.app.db.models import AuditLog, RFO


def _create_rfo(client):
    payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    response = client.post("/v1/rfo", json=payload)
    return response.json()["rfo_id"]


def test_close_rfo_creates_audit_log(client, session):
    rfo_id = _create_rfo(client)

    response = client.post(
        f"/v1/rfo/{rfo_id}/close",
        json={"reason": "buyer_done"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "CLOSED"
    assert payload["reason"] == "buyer_done"

    rfo = session.get(RFO, rfo_id)
    assert rfo.status == "CLOSED"
    assert rfo.status_reason == "buyer_done"

    audit = session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "rfo",
            AuditLog.entity_id == rfo_id,
            AuditLog.action == "close",
        )
    ).first()
    assert audit is not None
    assert audit.metadata_["reason"] == "buyer_done"


def test_award_requires_closed_rfo(client, session):
    rfo_id = _create_rfo(client)

    bad_response = client.post(f"/v1/rfo/{rfo_id}/award")
    assert bad_response.status_code == 400

    close_response = client.post(f"/v1/rfo/{rfo_id}/close")
    assert close_response.status_code == 200

    award_response = client.post(f"/v1/rfo/{rfo_id}/award")
    assert award_response.status_code == 200
    assert award_response.json()["status"] == "AWARDED"

    rfo = session.get(RFO, rfo_id)
    assert rfo.status == "AWARDED"

    audit_actions = [
        row.action
        for row in session.exec(
            select(AuditLog).where(
                AuditLog.entity_type == "rfo",
                AuditLog.entity_id == rfo_id,
            )
        ).all()
    ]
    assert "close" in audit_actions
    assert "award" in audit_actions


def test_reopen_rfo_from_closed(client, session):
    rfo_id = _create_rfo(client)

    close_response = client.post(f"/v1/rfo/{rfo_id}/close")
    assert close_response.status_code == 200

    reopen_response = client.post(f"/v1/rfo/{rfo_id}/reopen")
    assert reopen_response.status_code == 200
    assert reopen_response.json()["status"] == "OPEN"

    rfo = session.get(RFO, rfo_id)
    assert rfo.status == "OPEN"

    audit = session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "rfo",
            AuditLog.entity_id == rfo_id,
            AuditLog.action == "reopen",
        )
    ).first()
    assert audit is not None
