from intentbid.app.core.config import settings
from intentbid.app.core.rate_limit import rate_limiter


def test_rate_limit_enforced_for_vendor(client, monkeypatch):
    vendor_response = client.post("/v1/vendors/register", json={"name": "Acme"})
    api_key = vendor_response.json()["api_key"]

    monkeypatch.setattr(settings, "rate_limit_requests", 1)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)
    rate_limiter.reset()

    first = client.get("/v1/vendors/me/profile", headers={"X-API-Key": api_key})
    assert first.status_code == 200

    second = client.get("/v1/vendors/me/profile", headers={"X-API-Key": api_key})
    assert second.status_code == 429
