def test_create_rfo_syncs_constraints_from_explicit_fields(client):
    payload = {
        "category": "sneakers",
        "constraints": {"size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
        "budget_max": 180.0,
        "delivery_deadline_days": 5,
    }

    response = client.post("/v1/rfo", json=payload)

    assert response.status_code == 200

    rfo_id = response.json()["rfo_id"]
    detail = client.get(f"/v1/rfo/{rfo_id}")

    assert detail.status_code == 200

    data = detail.json()
    assert data["constraints"]["budget_max"] == 180.0
    assert data["constraints"]["delivery_deadline_days"] == 5
    assert data["constraints"]["size"] == 42
