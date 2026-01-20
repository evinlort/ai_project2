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


def test_sdk_register_buyer_sends_payload_and_returns_data():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/v1/buyers/register"
        payload = httpx.Response(200, content=request.content).json()
        assert payload["name"] == "BuyerCo"
        return httpx.Response(200, json={"buyer_id": 4, "api_key": "buyer_test"})

    transport = httpx.MockTransport(handler)
    client = IntentBidClient(base_url="https://example.com", transport=transport)
    response = client.register_buyer("BuyerCo")
    assert response["buyer_id"] == 4
    assert response["api_key"] == "buyer_test"


def test_sdk_list_rfos_passes_filters():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/v1/rfo"
        assert request.url.params["status"] == "OPEN"
        assert request.url.params["category"] == "sneakers"
        assert request.url.params["budget_min"] == "50"
        assert request.url.params["budget_max"] == "200"
        assert request.url.params["deadline_max"] == "7"
        return httpx.Response(200, json={"items": [], "total": 0, "limit": 20, "offset": 0})

    transport = httpx.MockTransport(handler)
    client = IntentBidClient(base_url="https://example.com", transport=transport)
    response = client.list_rfos(
        status="OPEN",
        category="sneakers",
        budget_min=50,
        budget_max=200,
        deadline_max=7,
    )
    assert response["items"] == []


def test_sdk_get_rfo_fetches_detail():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/v1/rfo/3"
        return httpx.Response(200, json={"id": 3, "status": "OPEN"})

    transport = httpx.MockTransport(handler)
    client = IntentBidClient(base_url="https://example.com", transport=transport)
    response = client.get_rfo(3)
    assert response["id"] == 3


def test_sdk_list_buyer_rfos_sets_buyer_key_header():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/v1/buyers/rfos"
        assert request.headers["X-Buyer-API-Key"] == "buyer_test"
        return httpx.Response(200, json={"items": [], "total": 0, "limit": 20, "offset": 0})

    transport = httpx.MockTransport(handler)
    client = IntentBidClient(base_url="https://example.com", transport=transport)
    response = client.list_buyer_rfos("buyer_test")
    assert response["items"] == []


def test_sdk_get_buyer_ranking_sets_buyer_key_header():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/v1/buyers/rfo/5/ranking"
        assert request.headers["X-Buyer-API-Key"] == "buyer_test"
        return httpx.Response(200, json={"rfo_id": 5, "offers": []})

    transport = httpx.MockTransport(handler)
    client = IntentBidClient(base_url="https://example.com", transport=transport)
    response = client.get_buyer_ranking(5, "buyer_test")
    assert response["rfo_id"] == 5
