from datetime import datetime
from pathlib import Path

import httpx
from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from intentbid.app.ui.api_client import UiApiClient

router = APIRouter(prefix="/buyer", tags=["buyer-dashboard"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _resolve_buyer_key(request: Request, form_api_key: str | None = None) -> str | None:
    return (
        form_api_key
        or request.query_params.get("buyer_api_key")
        or request.cookies.get("buyer_api_key")
    )


@router.get("/register", response_class=HTMLResponse)
async def buyer_register(request: Request):
    transport = httpx.ASGITransport(app=request.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/v1/buyers/register", json={"name": "Buyer"})
        response.raise_for_status()
        payload = response.json()

    buyer_api_key = payload["api_key"]
    response = templates.TemplateResponse(
        "buyer/register.html",
        {"request": request, "buyer_api_key": buyer_api_key},
    )
    response.set_cookie("buyer_api_key", buyer_api_key, httponly=True)
    return response


@router.get("/rfos/new", response_class=HTMLResponse)
def buyer_rfo_create_page(request: Request):
    buyer_api_key = request.cookies.get("buyer_api_key")
    return templates.TemplateResponse(
        "buyer/rfo_new.html",
        {"request": request, "buyer_api_key": buyer_api_key},
    )


@router.post("/rfos/new")
async def buyer_rfo_create_submit(
    request: Request,
    title: str | None = Form(None),
    summary: str | None = Form(None),
    category: str = Form(...),
    budget_max: float = Form(...),
    currency: str | None = Form(None),
    quantity: int | None = Form(None),
    location: str | None = Form(None),
    size: int | None = Form(None),
    delivery_deadline_days: int = Form(...),
    expires_at: str | None = Form(None),
    w_price: float = Form(...),
    w_delivery: float = Form(...),
    w_warranty: float = Form(...),
    buyer_api_key: str | None = Form(None),
):
    buyer_key = _resolve_buyer_key(request, buyer_api_key)
    title_value = title.strip() if title else None
    summary_value = summary.strip() if summary else None
    currency_value = currency.strip() if currency else None
    location_value = location.strip() if location else None
    expires_value = expires_at.strip() if expires_at else None

    constraints = {
        "budget_max": budget_max,
        "delivery_deadline_days": delivery_deadline_days,
    }
    if size is not None:
        constraints["size"] = size

    preferences = {
        "w_price": w_price,
        "w_delivery": w_delivery,
        "w_warranty": w_warranty,
    }
    payload = {
        "category": category,
        "constraints": constraints,
        "preferences": preferences,
        "title": title_value,
        "summary": summary_value,
        "budget_max": budget_max,
        "currency": currency_value,
        "delivery_deadline_days": delivery_deadline_days,
        "quantity": quantity,
        "location": location_value,
        "expires_at": expires_value,
    }

    transport = httpx.ASGITransport(app=request.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        api = UiApiClient(client)
        rfo_response = await api.create_request(payload, buyer_api_key=buyer_key)
    return RedirectResponse(
        url=f"/buyer/rfos/check?rfo_id={rfo_response['rfo_id']}",
        status_code=303,
    )


@router.get("/rfos", response_class=HTMLResponse)
async def buyer_rfo_list(request: Request):
    buyer_api_key = _resolve_buyer_key(request)
    error = None
    rfo_rows = []

    if not buyer_api_key:
        error = "Add your buyer API key to view requests."
    else:
        transport = httpx.ASGITransport(app=request.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            api = UiApiClient(client)
            try:
                response = await client.get(
                    "/v1/buyers/rfos",
                    headers={"X-Buyer-API-Key": buyer_api_key},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 401:
                    error = "Invalid buyer API key."
                else:
                    raise
            else:
                payload = response.json()
                for item in payload.get("items", []):
                    detail = await api.get_request(item["id"])
                    rfo_rows.append(
                        {
                            "rfo": item,
                            "offers_count": detail.get("offers_count", 0),
                        }
                    )

    response = templates.TemplateResponse(
        "buyer/rfo_list.html",
        {
            "request": request,
            "rfos": rfo_rows,
            "buyer_api_key": buyer_api_key,
            "error": error,
        },
    )
    if buyer_api_key and buyer_api_key != request.cookies.get("buyer_api_key"):
        response.set_cookie("buyer_api_key", buyer_api_key, httponly=True)
    return response


@router.get("/rfos/check", response_class=HTMLResponse)
async def buyer_rfo_check(
    request: Request,
    rfo_id: int | None = Query(None, ge=1),
):
    buyer_api_key = _resolve_buyer_key(request)
    rfo = None
    offers_count = 0
    error = None

    if rfo_id is not None:
        transport = httpx.ASGITransport(app=request.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            api = UiApiClient(client)
            try:
                rfo = await api.get_request(rfo_id)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    error = "RFO not found"
                else:
                    try:
                        error = exc.response.json().get("detail")
                    except ValueError:
                        error = exc.response.text
                    error = error or "Unable to load RFO"
            else:
                offers_count = rfo.get("offers_count", 0)
                created_at = rfo.get("created_at")
                if created_at:
                    try:
                        rfo["created_at"] = datetime.fromisoformat(created_at)
                    except ValueError:
                        pass

    return templates.TemplateResponse(
        "buyer/rfo_check.html",
        {
            "request": request,
            "rfo": rfo,
            "rfo_id": rfo_id,
            "offers_count": offers_count,
            "error": error,
            "buyer_api_key": buyer_api_key,
        },
    )


@router.get("/rfos/best", response_class=HTMLResponse)
async def buyer_best_offers(
    request: Request,
    rfo_id: int | None = Query(None, ge=1),
    top_k: int = Query(3, ge=1, le=50),
):
    rfo = None
    offer_rows = []
    error = None

    if rfo_id is not None:
        transport = httpx.ASGITransport(app=request.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            api = UiApiClient(client)
            try:
                rfo = await api.get_request(rfo_id)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    error = "RFO not found"
                else:
                    try:
                        error = exc.response.json().get("detail")
                    except ValueError:
                        error = exc.response.text
                    error = error or "Unable to load RFO"
            else:
                try:
                    best_payload = await api.get_best_offers(rfo_id, top_k)
                except httpx.HTTPStatusError as exc:
                    try:
                        error = exc.response.json().get("detail")
                    except ValueError:
                        error = exc.response.text
                    error = error or "Unable to load offers"
                else:
                    offer_rows = [
                        {
                            "offer": item["offer"],
                            "score": item["score"],
                            "explain": item.get("explain", {}),
                        }
                        for item in best_payload.get("top_offers", [])
                    ]

    return templates.TemplateResponse(
        "buyer/best_offers.html",
        {
            "request": request,
            "rfo": rfo,
            "rfo_id": rfo_id,
            "top_k": top_k,
            "offers": offer_rows,
            "error": error,
        },
    )


@router.get("/rfos/scoring", response_class=HTMLResponse)
async def buyer_scoring(
    request: Request,
    rfo_id: int | None = Query(None, ge=1),
):
    buyer_api_key = _resolve_buyer_key(request)
    buyer = None
    rfo = None
    offer_rows = []
    error = None

    if rfo_id is not None:
        if not buyer_api_key:
            error = "Add your buyer API key to view scoring."
        else:
            transport = httpx.ASGITransport(app=request.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                api = UiApiClient(client)
                try:
                    buyer_response = await client.get(
                        "/v1/buyers/me",
                        headers={"X-Buyer-API-Key": buyer_api_key},
                    )
                    buyer_response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 401:
                        error = "Invalid buyer API key."
                    else:
                        try:
                            error = exc.response.json().get("detail")
                        except ValueError:
                            error = exc.response.text
                        error = error or "Unable to load buyer"
                else:
                    buyer = buyer_response.json()
                    try:
                        rfo = await api.get_request(rfo_id)
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code == 404:
                            error = "RFO not found"
                        else:
                            try:
                                error = exc.response.json().get("detail")
                            except ValueError:
                                error = exc.response.text
                            error = error or "Unable to load RFO"
                    else:
                        try:
                            ranking_payload = await api.get_buyer_ranking(rfo_id, buyer_api_key)
                        except httpx.HTTPStatusError as exc:
                            try:
                                error = exc.response.json().get("detail")
                            except ValueError:
                                error = exc.response.text
                            error = error or "Unable to load ranking"
                        else:
                            offer_rows = [
                                {
                                    "offer": item["offer"],
                                    "score": item["score"],
                                    "explain": item.get("explain", {}),
                                }
                                for item in ranking_payload.get("offers", [])
                            ]

    response = templates.TemplateResponse(
        "buyer/rfo_scoring.html",
        {
            "request": request,
            "buyer": buyer,
            "buyer_api_key": buyer_api_key,
            "rfo": rfo,
            "rfo_id": rfo_id,
            "offers": offer_rows,
            "error": error,
        },
    )
    if buyer_api_key and buyer_api_key != request.cookies.get("buyer_api_key"):
        response.set_cookie("buyer_api_key", buyer_api_key, httponly=True)
    return response
