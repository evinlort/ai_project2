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

    def register_buyer(self, name: str) -> dict[str, Any]:
        response = self._client.post("/v1/buyers/register", json={"name": name})
        response.raise_for_status()
        return response.json()

    def create_rfo(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post("/v1/rfo", json=payload)
        response.raise_for_status()
        return response.json()

    def create_hardware_rfq(
        self,
        line_items: list[dict[str, Any]],
        constraints: dict[str, Any],
        compliance: dict[str, Any] | None = None,
        scoring_profile: str | None = None,
        *,
        category: str,
        preferences: dict[str, Any] | None = None,
        title: str | None = None,
        summary: str | None = None,
        buyer_api_key: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "category": category,
            "line_items": line_items,
            "constraints": constraints,
        }
        if preferences is not None:
            payload["preferences"] = preferences
        if compliance is not None:
            payload["compliance"] = compliance
        if scoring_profile is not None:
            payload["scoring_profile"] = scoring_profile
        if title is not None:
            payload["title"] = title
        if summary is not None:
            payload["summary"] = summary

        headers: dict[str, str] | None = None
        if buyer_api_key:
            headers = {"X-Buyer-API-Key": buyer_api_key}

        response = self._client.post("/v1/rfo", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def list_rfos(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
        budget_min: float | None = None,
        budget_max: float | None = None,
        deadline_max: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if status is not None:
            params["status"] = status
        if category is not None:
            params["category"] = category
        if budget_min is not None:
            params["budget_min"] = budget_min
        if budget_max is not None:
            params["budget_max"] = budget_max
        if deadline_max is not None:
            params["deadline_max"] = deadline_max
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.get("/v1/rfo", params=params or None)
        response.raise_for_status()
        return response.json()

    def get_rfo(self, rfo_id: int) -> dict[str, Any]:
        response = self._client.get(f"/v1/rfo/{rfo_id}")
        response.raise_for_status()
        return response.json()

    def submit_offer(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = self._auth_headers()
        response = self._client.post("/v1/offers", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def submit_hardware_offer(
        self,
        *,
        rfo_id: int,
        unit_price: float,
        currency: str,
        available_qty: int,
        lead_time_days: int,
        condition: str,
        warranty_months: int,
        return_days: int,
        traceability: dict[str, Any],
        shipping_cost: float | None = None,
        tax_estimate: float | None = None,
        valid_until: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "rfo_id": rfo_id,
            "unit_price": unit_price,
            "currency": currency,
            "available_qty": available_qty,
            "lead_time_days": lead_time_days,
            "condition": condition,
            "warranty_months": warranty_months,
            "return_days": return_days,
            "traceability": traceability,
        }
        if shipping_cost is not None:
            payload["shipping_cost"] = shipping_cost
        if tax_estimate is not None:
            payload["tax_estimate"] = tax_estimate
        if valid_until is not None:
            payload["valid_until"] = valid_until
        if metadata is not None:
            payload["metadata"] = metadata
        return self.submit_offer(payload)

    def get_vendor_profile(self) -> dict[str, Any]:
        headers = self._auth_headers()
        response = self._client.get("/v1/vendors/me/profile", headers=headers)
        response.raise_for_status()
        return response.json()

    def update_vendor_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = self._auth_headers()
        response = self._client.put("/v1/vendors/me/profile", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def list_vendor_offers(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        headers = self._auth_headers()
        response = self._client.get(
            "/v1/vendors/me/offers",
            params=params or None,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def get_best_offers(self, rfo_id: int, *, top_k: int = 3) -> dict[str, Any]:
        response = self._client.get(f"/v1/rfo/{rfo_id}/best", params={"top_k": top_k})
        response.raise_for_status()
        return response.json()

    def list_matches(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        headers = self._auth_headers()
        response = self._client.get(
            "/v1/vendors/me/matches",
            params=params or None,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def list_buyer_rfos(
        self,
        buyer_api_key: str,
        *,
        status: str | None = None,
        category: str | None = None,
        budget_min: float | None = None,
        budget_max: float | None = None,
        deadline_max: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if status is not None:
            params["status"] = status
        if category is not None:
            params["category"] = category
        if budget_min is not None:
            params["budget_min"] = budget_min
        if budget_max is not None:
            params["budget_max"] = budget_max
        if deadline_max is not None:
            params["deadline_max"] = deadline_max
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        headers = {"X-Buyer-API-Key": buyer_api_key}
        response = self._client.get("/v1/buyers/rfos", params=params or None, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_buyer_ranking(self, rfo_id: int, buyer_api_key: str) -> dict[str, Any]:
        headers = {"X-Buyer-API-Key": buyer_api_key}
        response = self._client.get(f"/v1/buyers/rfo/{rfo_id}/ranking", headers=headers)
        response.raise_for_status()
        return response.json()

    def get_ranking_explain(self, rfo_id: int, buyer_api_key: str | None = None) -> dict[str, Any]:
        headers = {"X-Buyer-API-Key": buyer_api_key} if buyer_api_key else None
        response = self._client.get(f"/v1/rfo/{rfo_id}/ranking/explain", headers=headers)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()

    def _auth_headers(self) -> dict[str, str]:
        if not self._api_key:
            return {}
        return {"X-API-Key": self._api_key}
