def _create_vendor_and_rfo(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    vendor_payload = vendor_response.json()

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    return vendor_payload["api_key"], rfo_response.json()["rfo_id"]


def _create_offer(client, api_key, rfo_id, price_amount, delivery_eta_days, warranty_months):
    offer_payload = {
        "rfo_id": rfo_id,
        "price_amount": price_amount,
        "currency": "USD",
        "delivery_eta_days": delivery_eta_days,
        "warranty_months": warranty_months,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": f"{price_amount}"},
    }
    response = client.post(
        "/v1/offers",
        json=offer_payload,
        headers={"X-API-Key": api_key},
    )
    return response.json()["offer_id"]


def test_update_scoring_weights_changes_ranking(client):
    api_key, rfo_id = _create_vendor_and_rfo(client)
    offer_a = _create_offer(client, api_key, rfo_id, 60.0, 3, 12)
    offer_b = _create_offer(client, api_key, rfo_id, 110.0, 1, 12)

    explain_response = client.get(f"/v1/rfo/{rfo_id}/ranking/explain")
    assert explain_response.status_code == 200
    explain_payload = explain_response.json()
    assert explain_payload["scoring_version"] == "v1"
    assert explain_payload["offers"][0]["offer_id"] == offer_a

    update_response = client.post(
        f"/v1/rfo/{rfo_id}/scoring",
        json={
            "weights": {"w_price": 0.1, "w_delivery": 0.8, "w_warranty": 0.1},
            "scoring_version": "v2",
        },
    )
    assert update_response.status_code == 200

    updated_explain = client.get(f"/v1/rfo/{rfo_id}/ranking/explain")
    assert updated_explain.status_code == 200
    updated_payload = updated_explain.json()
    assert updated_payload["scoring_version"] == "v2"
    assert updated_payload["offers"][0]["offer_id"] == offer_b
    assert updated_payload["offers"][0]["explain"]["weights"]["w_delivery"] == 0.8
