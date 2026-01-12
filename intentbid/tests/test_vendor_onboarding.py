def test_vendor_onboarding_status(client):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    vendor_payload = vendor_response.json()

    status_response = client.get(
        "/v1/vendors/onboarding/status",
        headers={"X-API-Key": vendor_payload["api_key"]},
    )
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["steps"]["api_key"] is True
    assert status_payload["steps"]["webhook"] is False
    assert status_payload["steps"]["test_call"] is False
    assert status_payload["steps"]["go_live"] is False

    webhook_response = client.post(
        "/v1/vendors/webhooks",
        json={"url": "https://example.com/webhook"},
        headers={"X-API-Key": vendor_payload["api_key"]},
    )
    assert webhook_response.status_code == 200

    updated_response = client.get(
        "/v1/vendors/onboarding/status",
        headers={"X-API-Key": vendor_payload["api_key"]},
    )
    updated_payload = updated_response.json()
    assert updated_payload["steps"]["webhook"] is True
