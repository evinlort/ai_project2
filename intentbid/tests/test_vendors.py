from intentbid.app.db.models import Vendor


def test_register_vendor_creates_api_key(client, session):
    response = client.post("/v1/vendors/register", json={"name": "Acme"})

    assert response.status_code == 200

    payload = response.json()
    assert payload["vendor_id"]
    assert payload["api_key"]

    vendor = session.get(Vendor, payload["vendor_id"])
    assert vendor is not None
    assert vendor.name == "Acme"
    assert vendor.api_key_hash != payload["api_key"]


def test_vendor_auth_requires_api_key(client):
    response = client.post("/v1/vendors/register", json={"name": "Acme"})
    payload = response.json()

    unauthorized = client.get("/v1/vendors/me")
    assert unauthorized.status_code == 401

    authorized = client.get(
        "/v1/vendors/me",
        headers={"X-API-Key": payload["api_key"]},
    )
    assert authorized.status_code == 200
    assert authorized.json()["vendor_id"] == payload["vendor_id"]
