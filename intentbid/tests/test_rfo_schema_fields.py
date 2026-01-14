from datetime import datetime, timezone


def _base_payload():
    return {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }


def test_rfo_create_includes_explicit_fields_in_detail(client):
    expires_at = datetime.now(timezone.utc).replace(microsecond=0)

    payload = _base_payload()
    payload.update(
        {
            "title": "Wholesale sneakers",
            "summary": "Bulk request for premium runners",
            "budget_max": 250.0,
            "currency": "USD",
            "delivery_deadline_days": 7,
            "quantity": 120,
            "location": "Berlin",
            "expires_at": expires_at.isoformat(),
        }
    )

    response = client.post("/v1/rfo", json=payload)

    assert response.status_code == 200

    rfo_id = response.json()["rfo_id"]
    detail = client.get(f"/v1/rfo/{rfo_id}")

    assert detail.status_code == 200

    data = detail.json()
    assert data["title"] == "Wholesale sneakers"
    assert data["summary"] == "Bulk request for premium runners"
    assert data["budget_max"] == 250.0
    assert data["currency"] == "USD"
    assert data["delivery_deadline_days"] == 7
    assert data["quantity"] == 120
    assert data["location"] == "Berlin"
    assert data["expires_at"] == expires_at.isoformat()


def test_rfo_create_rejects_negative_budget_max(client):
    payload = _base_payload()
    payload["budget_max"] = -10.0

    response = client.post("/v1/rfo", json=payload)

    assert response.status_code == 422


def test_rfo_create_rejects_non_positive_deadline(client):
    payload = _base_payload()
    payload["delivery_deadline_days"] = 0

    response = client.post("/v1/rfo", json=payload)

    assert response.status_code == 422
