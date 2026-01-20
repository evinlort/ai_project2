def test_landing_page_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "IntentBid" in response.text
    assert "Buyer request" in response.text


def test_vendor_dashboard_links_to_landing(client):
    response = client.get("/dashboard/login")

    assert response.status_code == 200
    assert 'href="/"' in response.text


def test_buyer_dashboard_links_to_landing(client):
    response = client.get("/buyer/rfos/new")

    assert response.status_code == 200
    assert 'href="/"' in response.text
