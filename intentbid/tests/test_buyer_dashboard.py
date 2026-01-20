def test_buyer_rfo_create_page(client):
    response = client.get("/buyer/rfos/new")

    assert response.status_code == 200
    assert "Create a new RFO" in response.text


def test_buyer_register_page_sets_api_key_cookie(client):
    response = client.get("/buyer/register")

    assert response.status_code == 200
    assert "Buyer API key" in response.text
    buyer_api_key = response.cookies.get("buyer_api_key")
    assert buyer_api_key
    assert buyer_api_key in response.text


def test_buyer_rfo_create_redirects_to_check(client):
    form_data = {
        "category": "sneakers",
        "budget_max": 120,
        "size": 42,
        "delivery_deadline_days": 3,
        "w_price": 0.6,
        "w_delivery": 0.3,
        "w_warranty": 0.1,
    }

    response = client.post("/buyer/rfos/new", data=form_data, allow_redirects=False)

    assert response.status_code in {302, 303}
    assert response.headers["location"].startswith("/buyer/rfos/check")
    assert "rfo_id=" in response.headers["location"]


def test_buyer_rfo_create_sends_explicit_fields(client):
    form_data = {
        "title": "Bulk sneaker order",
        "summary": "Need a bulk order for an upcoming launch.",
        "category": "sneakers",
        "budget_max": 180,
        "currency": "USD",
        "quantity": 250,
        "location": "Berlin",
        "delivery_deadline_days": 5,
        "expires_at": "2099-01-01T12:00",
        "w_price": 0.6,
        "w_delivery": 0.3,
        "w_warranty": 0.1,
    }

    response = client.post("/buyer/rfos/new", data=form_data, allow_redirects=False)

    assert response.status_code in {302, 303}
    location = response.headers["location"]
    rfo_id = int(parse_qs(urlparse(location).query)["rfo_id"][0])
    rfo_detail = client.get(f"/v1/rfo/{rfo_id}").json()

    assert rfo_detail["title"] == form_data["title"]
    assert rfo_detail["summary"] == form_data["summary"]
    assert rfo_detail["budget_max"] == form_data["budget_max"]
    assert rfo_detail["currency"] == form_data["currency"]
    assert rfo_detail["quantity"] == form_data["quantity"]
    assert rfo_detail["location"] == form_data["location"]
    assert rfo_detail["delivery_deadline_days"] == form_data["delivery_deadline_days"]
    assert rfo_detail["expires_at"]


def test_buyer_rfo_check_page_shows_details(client):
    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    rfo_id = rfo_response.json()["rfo_id"]

    response = client.get(f"/buyer/rfos/check?rfo_id={rfo_id}")

    assert response.status_code == 200
    assert rfo_payload["category"] in response.text


def test_buyer_best_offers_page_lists_offers(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    rfo_id = rfo_response.json()["rfo_id"]

    offer_payload = {
        "rfo_id": rfo_id,
        "price_amount": 99.0,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "B"},
    }
    client.post("/v1/offers", json=offer_payload, headers={"X-API-Key": api_key})

    response = client.get(f"/buyer/rfos/best?rfo_id={rfo_id}&top_k=1")

    assert response.status_code == 200
    assert "Best offers" in response.text
    assert "USD" in response.text


def test_buyer_scoring_page_shows_rankings(client):
    buyer_response = client.post("/v1/buyers/register", json={"name": "Buyer"})
    buyer_key = buyer_response.json()["api_key"]

    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    rfo_response = client.post("/v1/rfo", json=rfo_payload)
    rfo_id = rfo_response.json()["rfo_id"]

    offer_payload = {
        "rfo_id": rfo_id,
        "price_amount": 99.0,
        "currency": "USD",
        "delivery_eta_days": 2,
        "warranty_months": 12,
        "return_days": 30,
        "stock": True,
        "metadata": {"sku": "B"},
    }
    client.post("/v1/offers", json=offer_payload, headers={"X-API-Key": api_key})

    response = client.get(
        f"/buyer/rfos/scoring?rfo_id={rfo_id}&buyer_api_key={buyer_key}"
    )

    assert response.status_code == 200
    assert "Buyer scoring" in response.text
    assert "Score" in response.text
from urllib.parse import parse_qs, urlparse
