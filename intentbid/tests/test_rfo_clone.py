
def _register_buyer(client):
    return client.post("/v1/buyers/register", json={"name": "Buyer"}).json()


def test_clone_copies_line_items_and_constraints(client):
    buyer = _register_buyer(client)
    payload = {
        "category": "GPU",
        "constraints": {"budget_max": 50000, "delivery_deadline_days": 5},
        "preferences": {"w_price": 0.5, "w_delivery": 0.3, "w_warranty": 0.2},
        "line_items": [{"mpn": "H100-SXM5-80GB", "quantity": 1}],
        "compliance": {"export_control_ack": True},
        "scoring_profile": "balanced",
    }

    create = client.post(
        "/v1/rfo",
        json=payload,
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )
    rfo_id = create.json()["rfo_id"]

    clone = client.post(
        f"/v1/rfo/{rfo_id}/clone",
        headers={"X-Buyer-API-Key": buyer["api_key"]},
    )
    assert clone.status_code == 200

    cloned_id = clone.json()["rfo_id"]
    detail = client.get(f"/v1/rfo/{cloned_id}")
    assert detail.status_code == 200

    data = detail.json()
    assert data["category"] == payload["category"]
    assert data["constraints"] == payload["constraints"]
    assert data["line_items"] == payload["line_items"]
    assert data["compliance"] == payload["compliance"]
    assert data["scoring_profile"] == payload["scoring_profile"]
