from sqlmodel import select

from intentbid.app.db.models import VendorApiKey


def test_create_vendor_key_and_revoke(client, session):
    response = client.post("/v1/vendors/register", json={"name": "Acme"})
    payload = response.json()

    create_response = client.post(
        "/v1/vendors/keys",
        headers={"X-API-Key": payload["api_key"]},
    )

    assert create_response.status_code == 200

    key_payload = create_response.json()
    assert key_payload["key_id"]
    assert key_payload["api_key"]
    assert key_payload["status"] == "active"

    key = session.get(VendorApiKey, key_payload["key_id"])
    assert key is not None
    assert key.vendor_id == payload["vendor_id"]
    assert key.status == "active"

    authorized = client.get(
        "/v1/vendors/me",
        headers={"X-API-Key": key_payload["api_key"]},
    )
    assert authorized.status_code == 200

    revoke_response = client.post(
        f"/v1/vendors/keys/{key_payload['key_id']}/revoke",
        headers={"X-API-Key": payload["api_key"]},
    )
    assert revoke_response.status_code == 200

    revoked_payload = revoke_response.json()
    assert revoked_payload["status"] == "revoked"
    assert revoked_payload["revoked_at"] is not None

    unauthorized = client.get(
        "/v1/vendors/me",
        headers={"X-API-Key": key_payload["api_key"]},
    )
    assert unauthorized.status_code == 401

    session.refresh(key)
    assert key.status == "revoked"
    assert key.revoked_at is not None


def test_last_used_at_updates_on_auth(client, session):
    response = client.post("/v1/vendors/register", json={"name": "Acme"})
    payload = response.json()

    key = session.exec(
        select(VendorApiKey).where(VendorApiKey.vendor_id == payload["vendor_id"])
    ).first()
    assert key is not None
    assert key.last_used_at is None

    authorized = client.get(
        "/v1/vendors/me",
        headers={"X-API-Key": payload["api_key"]},
    )
    assert authorized.status_code == 200

    session.refresh(key)
    assert key.last_used_at is not None


def test_revoke_other_vendor_key_is_not_found(client):
    vendor_a = client.post("/v1/vendors/register", json={"name": "Vendor A"}).json()
    vendor_b = client.post("/v1/vendors/register", json={"name": "Vendor B"}).json()

    key_response = client.post(
        "/v1/vendors/keys",
        headers={"X-API-Key": vendor_a["api_key"]},
    )
    key_payload = key_response.json()

    revoke_response = client.post(
        f"/v1/vendors/keys/{key_payload['key_id']}/revoke",
        headers={"X-API-Key": vendor_b["api_key"]},
    )
    assert revoke_response.status_code == 404
