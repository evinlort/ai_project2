def test_ru_index_page(client):
    response = client.get("/ru/")

    assert response.status_code == 200
    assert 'lang="ru"' in response.text


def test_ru_dashboard_login_page(client):
    response = client.get("/ru/dashboard/login")

    assert response.status_code == 200
    assert 'lang="ru"' in response.text


def test_ru_dashboard_rfos_requires_api_key(client):
    response = client.get("/ru/dashboard/rfos", allow_redirects=False)

    assert response.status_code in {302, 303}
    assert response.headers["location"].endswith("/ru/dashboard/login")


def test_ru_dashboard_rfos_lists_open_rfos(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    rfo_payload = {
        "category": "sneakers",
        "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
        "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    }
    client.post("/v1/rfo", json=rfo_payload)

    response = client.get(f"/ru/dashboard/rfos?api_key={api_key}")

    assert response.status_code == 200
    assert rfo_payload["category"] in response.text
