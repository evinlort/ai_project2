from datetime import datetime, timezone


def _create_rfo(client, category, budget_max, deadline_days, status="OPEN"):
    payload = {
        "category": category,
        "constraints": {"size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
        "budget_max": budget_max,
        "currency": "USD",
        "delivery_deadline_days": deadline_days,
        "title": f"{category} request",
        "expires_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    response = client.post("/v1/rfo", json=payload)
    rfo_id = response.json()["rfo_id"]

    if status != "OPEN":
        client.post(f"/v1/rfo/{rfo_id}/close")

    return rfo_id


def test_list_rfos_filters_by_status_category_budget_and_deadline(client):
    rfo_open = _create_rfo(client, "sneakers", 200.0, 5)
    _create_rfo(client, "bags", 80.0, 10, status="CLOSED")
    rfo_match = _create_rfo(client, "sneakers", 150.0, 3)

    response = client.get(
        "/v1/rfo",
        params={
            "status": "OPEN",
            "category": "sneakers",
            "budget_min": 100,
            "budget_max": 180,
            "deadline_max": 4,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == rfo_match
    assert data["items"][0]["budget_max"] == 150.0
    assert data["items"][0]["delivery_deadline_days"] == 3
    assert rfo_open not in [item["id"] for item in data["items"]]


def test_list_rfos_supports_pagination(client):
    _create_rfo(client, "sneakers", 200.0, 5)
    _create_rfo(client, "bags", 80.0, 10)

    response = client.get("/v1/rfo", params={"limit": 1, "offset": 1})

    assert response.status_code == 200

    data = response.json()
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert data["total"] == 2
    assert len(data["items"]) == 1
