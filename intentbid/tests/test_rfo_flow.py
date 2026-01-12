
def test_rfo_flow_best_offers_sorted(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    vendor_payload = vendor_response.json()

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    rfo_id = rfo_response.json()["rfo_id"]

    offer_a = {
        "rfo_id": rfo_id,
        "price_amount": 100.0,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "A"},
    }
    offer_b = {
        "rfo_id": rfo_id,
        "price_amount": 90.0,
        "currency": "USD",
        "delivery_eta_days": 1,
        "warranty_months": 6,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "B"},
    }

    headers = {"X-API-Key": vendor_payload["api_key"]}
    offer_a_response = client.post("/v1/offers", json=offer_a, headers=headers)
    offer_b_response = client.post("/v1/offers", json=offer_b, headers=headers)

    offer_a_id = offer_a_response.json()["offer_id"]
    offer_b_id = offer_b_response.json()["offer_id"]

    best_response = client.get(f"/v1/rfo/{rfo_id}/best?top_k=2")

    assert best_response.status_code == 200

    data = best_response.json()
    assert data["rfo_id"] == rfo_id

    top_offers = data["top_offers"]
    assert len(top_offers) == 2
    assert top_offers[0]["score"] >= top_offers[1]["score"]
    assert top_offers[0]["offer_id"] == offer_b_id
    assert top_offers[1]["offer_id"] == offer_a_id
    assert "explain" in top_offers[0]
    assert "offer" in top_offers[0]
