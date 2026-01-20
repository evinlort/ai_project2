import httpx


class UiApiClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        response = await self._client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()

    async def list_requests(self, params: dict | None = None) -> dict:
        return await self._request("GET", "/v1/rfo", params=params)

    async def get_request(self, rfo_id: int) -> dict:
        return await self._request("GET", f"/v1/rfo/{rfo_id}")

    async def get_vendor_me(self, api_key: str) -> dict:
        headers = {"X-API-Key": api_key}
        return await self._request("GET", "/v1/vendors/me", headers=headers)

    async def create_request(self, payload: dict, buyer_api_key: str | None = None) -> dict:
        headers = {"X-Buyer-API-Key": buyer_api_key} if buyer_api_key else None
        return await self._request("POST", "/v1/rfo", json=payload, headers=headers)

    async def submit_offer(self, api_key: str, payload: dict) -> dict:
        headers = {"X-API-Key": api_key}
        return await self._request("POST", "/v1/offers", json=payload, headers=headers)

    async def list_vendor_offers(self, api_key: str, params: dict | None = None) -> dict:
        headers = {"X-API-Key": api_key}
        return await self._request(
            "GET",
            "/v1/vendors/me/offers",
            headers=headers,
            params=params,
        )

    async def get_best_offers(self, rfo_id: int, top_k: int | None = None) -> dict:
        params = {"top_k": top_k} if top_k is not None else None
        return await self._request("GET", f"/v1/rfo/{rfo_id}/best", params=params)

    async def get_buyer_ranking(self, rfo_id: int, buyer_api_key: str) -> dict:
        headers = {"X-Buyer-API-Key": buyer_api_key}
        return await self._request(
            "GET",
            f"/v1/buyers/rfo/{rfo_id}/ranking",
            headers=headers,
        )
