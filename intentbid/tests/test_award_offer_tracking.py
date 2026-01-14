from intentbid.app.db.models import Offer, RFO


def test_award_rfo_sets_offer_winner_fields(client, session):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    rfo_id = rfo_response.json()["rfo_id"]

    offer_payload = {
        "rfo_id": rfo_id,
        "price_amount": 99.0,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "B"},
    }
    offer_response = client.post(
        "/v1/offers", json=offer_payload, headers={"X-API-Key": api_key}
    )
    offer_id = offer_response.json()["offer_id"]

    close_response = client.post(f"/v1/rfo/{rfo_id}/close")
    assert close_response.status_code == 200

    award_response = client.post(
        f"/v1/rfo/{rfo_id}/award", json={"offer_id": offer_id}
    )
    assert award_response.status_code == 200

    rfo = session.get(RFO, rfo_id)
    offer = session.get(Offer, offer_id)

    assert rfo is not None
    assert offer is not None
    assert rfo.awarded_offer_id == offer_id
    assert offer.status == "awarded"
    assert offer.is_awarded is True
