import httpx

from intentbid.sdk.client import IntentBidClient


def test_sdk_register_vendor_sends_payload_and_returns_data():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/v1/vendors/register"
        payload = httpx.Response(200, content=request.content).json()
        assert payload["name"] == "Acme"
        return httpx.Response(200, json={"vendor_id": 1, "api_key": "sk_test"})

    transport = httpx.MockTransport(handler)
    client = IntentBidClient(base_url="https://example.com", transport=transport)
    response = client.register_vendor("Acme")
    assert response["vendor_id"] == 1
    assert response["api_key"] == "sk_test"


def test_sdk_submit_offer_sets_api_key_header():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/v1/offers"
        assert request.headers["X-API-Key"] == "sk_test"
        return httpx.Response(200, json={"offer_id": 10})

    transport = httpx.MockTransport(handler)
    client = IntentBidClient(base_url="https://example.com", api_key="sk_test", transport=transport)
    response = client.submit_offer(
        {
            "rfo_id": 1,
            "price_amount": 100.0,
            "currency": "USD",
            "delivery_eta_days": 2,
            "warranty_months": 12,
            "return_days": 30,
            "stock": True,
            "metadata": {"sku": "ABC"},
        }
    )
    assert response["offer_id"] == 10


def test_sdk_get_best_offers_with_top_k():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/v1/rfo/1/best"
        assert request.url.params["top_k"] == "2"
        return httpx.Response(200, json={"rfo_id": 1, "top_offers": []})

    transport = httpx.MockTransport(handler)
    client = IntentBidClient(base_url="https://example.com", transport=transport)
    response = client.get_best_offers(1, top_k=2)
    assert response["rfo_id"] == 1
