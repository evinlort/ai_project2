from sqlmodel import select

from intentbid.app.db.models import AuditLog


def test_award_records_expected_fee_in_audit(client, session):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "delivery_deadline_days": 3, "transaction_fee_percent": 1.0},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
        "quantity": 2,
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    rfo_id = rfo_response.json()["rfo_id"]

    offer_payload = {
        "rfo_id": rfo_id,
        "price_amount": 100.0,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "ABC"},
    }
    offer_response = client.post("/v1/offers", json=offer_payload, headers={"X-API-Key": api_key})
    offer_id = offer_response.json()["offer_id"]

    client.post(f"/v1/rfo/{rfo_id}/close", json={})
    award = client.post(f"/v1/rfo/{rfo_id}/award", json={"offer_id": offer_id})
    assert award.status_code == 200

    audit = session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "rfo",
            AuditLog.entity_id == rfo_id,
            AuditLog.action == "award",
        )
    ).first()
    assert audit is not None
    assert audit.metadata_["expected_fee"] == 2.0
