
def test_create_rfo_returns_id_and_status(client):
    payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }

    response = client.post("/v1/rfo", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["rfo_id"]
    assert data["status"] == "OPEN"


def test_get_rfo_returns_details_and_offers_count(client):
    payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    create_response = client.post("/v1/rfo", json=payload)

    rfo_id = create_response.json()["rfo_id"]

    response = client.get(f"/v1/rfo/{rfo_id}")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == rfo_id
    assert data["category"] == payload["category"]
    assert data["constraints"] == payload["constraints"]
    assert data["preferences"] == payload["preferences"]
    assert data["offers_count"] == 0
