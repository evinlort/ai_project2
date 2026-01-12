from typing import Any

import httpx


class IntentBidClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._client = httpx.Client(
            base_url=self._base_url,
            transport=transport,
            timeout=timeout,
        )

    def register_vendor(self, name: str) -> dict[str, Any]:
        response = self._client.post("/v1/vendors/register", json={"name": name})
        response.raise_for_status()
        return response.json()

    def create_rfo(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post("/v1/rfo", json=payload)
        response.raise_for_status()
        return response.json()

    def submit_offer(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = self._auth_headers()
        response = self._client.post("/v1/offers", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_best_offers(self, rfo_id: int, *, top_k: int = 3) -> dict[str, Any]:
        response = self._client.get(f"/v1/rfo/{rfo_id}/best", params={"top_k": top_k})
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()

    def _auth_headers(self) -> dict[str, str]:
        if not self._api_key:
            return {}
        return {"X-API-Key": self._api_key}
