import httpx
import pytest

from intentbid.app.main import app
from intentbid.app.ui.api_client import UiApiClient


@pytest.mark.anyio
async def test_ui_api_client_flow():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        api = UiApiClient(client)

        rfo_payload = {
            "category": "sneakers",
            "constraints": {"budget_max": 120, "size": 42},
            "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
        }
        create_payload = await api.create_request(rfo_payload)
        rfo_id = create_payload["rfo_id"]

        detail = await api.get_request(rfo_id)
        assert detail["id"] == rfo_id

        listed = await api.list_requests()
        assert any(item["id"] == rfo_id for item in listed["items"])

        vendor_response = await client.post("/v1/vendors/register", json={"name": "Acme"})
        vendor_api_key = vendor_response.json()["api_key"]

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
        offer_response = await api.submit_offer(vendor_api_key, offer_payload)
        assert offer_response["offer_id"]

        vendor_offers = await api.list_vendor_offers(vendor_api_key)
        assert vendor_offers["total"] == 1

        best_offers = await api.get_best_offers(rfo_id, top_k=1)
        assert best_offers["top_offers"]

        buyer_response = await client.post("/v1/buyers/register", json={"name": "Buyer"})
        buyer_api_key = buyer_response.json()["api_key"]

        ranking = await api.get_buyer_ranking(rfo_id, buyer_api_key)
        assert ranking["offers"]
