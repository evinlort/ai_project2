from intentbid.app.db.models import RFO


def test_create_rfo_attaches_buyer(client, session):
    buyer_response = client.post("/v1/buyers/register", json={"name": "Buyer"})
    buyer_payload = buyer_response.json()

    payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }

    response = client.post(
        "/v1/rfo",
        json=payload,
        headers={"X-Buyer-API-Key": buyer_payload["api_key"]},
    )

    assert response.status_code == 200

    rfo_id = response.json()["rfo_id"]
    rfo = session.get(RFO, rfo_id)
    assert rfo is not None
    assert rfo.buyer_id == buyer_payload["buyer_id"]


def test_create_rfo_allows_anonymous_requests(client, session):
    payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }

    response = client.post("/v1/rfo", json=payload)

    assert response.status_code == 200

    rfo_id = response.json()["rfo_id"]
    rfo = session.get(RFO, rfo_id)
    assert rfo is not None
    assert rfo.buyer_id is None
