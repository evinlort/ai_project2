
def test_dashboard_login_page(client):
    response = client.get("/dashboard/login")

    assert response.status_code == 200


def test_dashboard_rfos_requires_api_key(client):
    response = client.get("/dashboard/rfos", allow_redirects=False)

    assert response.status_code in {302, 303}
    assert response.headers["location"].endswith("/dashboard/login")


def test_dashboard_rfos_lists_open_rfos(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    client.post("/v1/rfo", json=rfo_payload)

    response = client.get(f"/dashboard/rfos?api_key={api_key}")

    assert response.status_code == 200
    assert rfo_payload["category"] in response.text


def test_dashboard_api_list_requires_api_key(client):
    response = client.get("/dashboard/apis", allow_redirects=False)

    assert response.status_code in {302, 303}
    assert response.headers["location"].endswith("/dashboard/login")


def test_dashboard_api_list_shows_endpoints(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    response = client.get(f"/dashboard/apis?api_key={api_key}")

    assert response.status_code == 200
    assert "Vendor registration" in response.text
    assert "/v1/vendors/register" in response.text


def test_dashboard_api_detail_page(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    response = client.get(f"/dashboard/apis/vendor-registration?api_key={api_key}")

    assert response.status_code == 200
    assert "Vendor registration" in response.text
    assert "POST /v1/vendors/register" in response.text


def test_dashboard_login_rejects_invalid_key(client):
    response = client.post(
        "/dashboard/login",
        data={"api_key": "bad-key"},
        allow_redirects=False,
    )

    assert response.status_code == 401
    assert "Invalid API key" in response.text


def test_dashboard_rfos_has_filters(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    response = client.get(f"/dashboard/rfos?api_key={api_key}")

    assert response.status_code == 200
    assert 'name="category"' in response.text
    assert 'name="budget_min"' in response.text
    assert 'name="budget_max"' in response.text
    assert 'name="deadline_max"' in response.text


def test_dashboard_rfo_detail_lists_offers(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42},
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

    response = client.get(f"/dashboard/rfos/{rfo_id}?api_key={api_key}")

    assert response.status_code == 200
    assert "USD" in response.text
