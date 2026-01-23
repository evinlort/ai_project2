
def test_end_to_end_rfo_offer_award_flow(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    assert rfo_response.status_code == 200
    rfo_id = rfo_response.json()["rfo_id"]

    offer_payload = {
        "rfo_id": rfo_id,
        "price_amount": 99.0,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "ABC"},
    }
    offer_response = client.post("/v1/offers", json=offer_payload, headers={"X-API-Key": api_key})
    assert offer_response.status_code == 200
    offer_id = offer_response.json()["offer_id"]

    ranking = client.get(f"/v1/rfo/{rfo_id}/ranking/explain")
    assert ranking.status_code == 200
    assert ranking.json()["offers"][0]["offer_id"] == offer_id

    close_response = client.post(f"/v1/rfo/{rfo_id}/close", json={})
    assert close_response.status_code == 200

    award_response = client.post(f"/v1/rfo/{rfo_id}/award", json={"offer_id": offer_id})
    assert award_response.status_code == 200
    assert award_response.json()["status"] == "AWARDED"
