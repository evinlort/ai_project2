from datetime import datetime, timedelta, timezone

from intentbid.app.db.models import Offer


def _hardware_rfo_payload():
    return {
        "category": "GPU",
        "constraints": {
            "budget_max": 30000,
            "currency": "USD",
            "delivery_deadline_days": 7,
            "region": "US",
            "traceability_required": True,
        },
        "preferences": {"w_price": 0.5, "w_delivery": 0.3, "w_warranty": 0.2},
        "line_items": [
            {
                "mpn": "H100-SXM5-80GB",
                "quantity": 2,
                "required_specs": {"vram_gb": 80, "form_factor": "SXM"},
            }
        ],
        "compliance": {"export_control_ack": True},
        "scoring_profile": "balanced",
    }


def _register_vendor(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    payload = vendor_response.json()
    return payload["api_key"], payload["vendor_id"]


def test_create_hardware_rfo_with_line_items(client):
    payload = _hardware_rfo_payload()

    response = client.post("/v1/rfo", json=payload)

    assert response.status_code == 200

    rfo_id = response.json()["rfo_id"]
    detail = client.get(f"/v1/rfo/{rfo_id}")

    assert detail.status_code == 200

    data = detail.json()
    assert data["category"] == "GPU"
    assert data["line_items"] == payload["line_items"]
    assert data["constraints"]["budget_max"] == 30000
    assert data["compliance"]["export_control_ack"] is True
    assert data["scoring_profile"] == "balanced"


def test_submit_hardware_offer_with_traceability(client, session):
    api_key, vendor_id = _register_vendor(client)
    rfo_response = client.post("/v1/rfo", json=_hardware_rfo_payload())
    rfo_id = rfo_response.json()["rfo_id"]

    valid_until = (datetime.now(timezone.utc) + timedelta(days=3)).replace(microsecond=0)
    payload = {
        "rfo_id": rfo_id,
        "unit_price": 28000.0,
        "currency": "USD",
        "available_qty": 4,
        "lead_time_days": 5,
        "condition": "new",
        "warranty_months": 12,
        "return_days": 30,
        "traceability": {
            "authorized_channel": True,
            "invoices_available": True,
            "serials_available": True,
            "notes": "Authorized distributor batch.",
        },
        "valid_until": valid_until.isoformat(),
    }

    response = client.post(
        "/v1/offers",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 200

    offer = session.get(Offer, response.json()["offer_id"])
    assert offer is not None
    assert offer.vendor_id == vendor_id
    assert offer.rfo_id == rfo_id
    assert offer.available_qty == 4
    assert offer.lead_time_days == 5
    assert offer.traceability["authorized_channel"] is True
    assert offer.valid_until == valid_until


def test_scoring_explain_includes_hardware_breakdown(client):
    api_key, _ = _register_vendor(client)
    rfo_response = client.post("/v1/rfo", json=_hardware_rfo_payload())
    rfo_id = rfo_response.json()["rfo_id"]

    offer_payload = {
        "rfo_id": rfo_id,
        "unit_price": 25000.0,
        "currency": "USD",
        "available_qty": 2,
        "lead_time_days": 3,
        "condition": "new",
        "warranty_months": 24,
        "return_days": 30,
        "traceability": {
            "authorized_channel": True,
            "invoices_available": True,
            "serials_available": True,
        },
    }

    offer_response = client.post(
        "/v1/offers",
        json=offer_payload,
        headers={"X-API-Key": api_key},
    )
    assert offer_response.status_code == 200

    best = client.get(f"/v1/rfo/{rfo_id}/best", params={"top_k": 1})
    assert best.status_code == 200
    best_explain = best.json()["top_offers"][0]["explain"]

    for key in (
        "price_score",
        "lead_time_score",
        "warranty_score",
        "traceability_score",
        "vendor_reputation_score",
        "components",
    ):
        assert key in best_explain

    ranking = client.get(f"/v1/rfo/{rfo_id}/ranking/explain")
    assert ranking.status_code == 200
    explain = ranking.json()["offers"][0]["explain"]
    components = explain["components"]

    for key in (
        "price_score",
        "lead_time_score",
        "warranty_score",
        "traceability_score",
        "vendor_reputation_score",
    ):
        assert key in components
    assert explain["penalties"] == []
