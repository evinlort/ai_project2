def test_buyer_rfo_list_requires_ownership(client):
    buyer_one = client.post("/v1/buyers/register", json={"name": "Buyer One"}).json()
    buyer_two = client.post("/v1/buyers/register", json={"name": "Buyer Two"}).json()

    payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }

    rfo_one = client.post(
        "/v1/rfo",
        json=payload,
        headers={"X-Buyer-API-Key": buyer_one["api_key"]},
    ).json()
    client.post(
        "/v1/rfo",
        json=payload,
        headers={"X-Buyer-API-Key": buyer_two["api_key"]},
    )
    client.post("/v1/rfo", json=payload)

    response = client.get(
        "/v1/buyers/rfos",
        headers={"X-Buyer-API-Key": buyer_one["api_key"]},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == rfo_one["rfo_id"]
