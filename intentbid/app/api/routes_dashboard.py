from datetime import datetime
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from intentbid.app.db.session import get_session
from intentbid.app.ui.api_client import UiApiClient
from intentbid.app.api.api_docs import get_api_doc, list_api_docs

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _resolve_api_key(request: Request, form_api_key: str | None = None) -> str | None:
    return form_api_key or request.query_params.get("api_key") or request.cookies.get("api_key")


async def _fetch_vendor(request: Request, api_key: str) -> dict | None:
    transport = httpx.ASGITransport(app=request.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        api = UiApiClient(client)
        try:
            return await api.get_vendor_me(api_key)
        except httpx.HTTPStatusError:
            return None


async def _get_vendor(request: Request, form_api_key: str | None = None):
    api_key = _resolve_api_key(request, form_api_key)
    if not api_key:
        return None, None

    vendor = await _fetch_vendor(request, api_key)
    return vendor, api_key


@router.get("/login", response_class=HTMLResponse)
def dashboard_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def dashboard_login_submit(
    request: Request,
    api_key: str = Form(...),
):
    vendor = await _fetch_vendor(request, api_key)
    if not vendor:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid API key"},
            status_code=401,
        )

    response = RedirectResponse(url="/dashboard/rfos", status_code=303)
    response.set_cookie("api_key", api_key, httponly=True)
    return response


@router.get("/rfos", response_class=HTMLResponse)
async def dashboard_rfos(request: Request, session: Session = Depends(get_session)):
    vendor, api_key = await _get_vendor(request)
    if not vendor:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    params = {"status": "OPEN"}
    for key in ("category", "budget_min", "budget_max", "deadline_max"):
        value = request.query_params.get(key)
        if value:
            params[key] = value

    transport = httpx.ASGITransport(app=request.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        api = UiApiClient(client)
        rfo_payload = await api.list_requests(params=params)

    rfos = rfo_payload.get("items", [])
    for rfo in rfos:
        created_at = rfo.get("created_at")
        if created_at:
            rfo["created_at"] = datetime.fromisoformat(created_at)

    response = templates.TemplateResponse(
        "rfos.html",
        {"request": request, "rfos": rfos, "vendor": vendor, "api_key": api_key},
    )
    if api_key and api_key != request.cookies.get("api_key"):
        response.set_cookie("api_key", api_key, httponly=True)
    return response


@router.get("/rfos/{rfo_id}", response_class=HTMLResponse)
async def dashboard_rfo_detail(
    request: Request,
    rfo_id: int,
    session: Session = Depends(get_session),
):
    vendor, api_key = await _get_vendor(request)
    if not vendor:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    transport = httpx.ASGITransport(app=request.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        api = UiApiClient(client)
        try:
            rfo = await api.get_request(rfo_id)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail="RFO not found") from exc
            raise
        vendor_offers = await api.list_vendor_offers(api_key)

    offers = [
        {
            "id": item["offer_id"],
            "price_amount": item["price_amount"],
            "currency": item["currency"],
            "delivery_eta_days": item["delivery_eta_days"],
            "warranty_months": item["warranty_months"],
            "return_days": item["return_days"],
            "stock": item["stock"],
        }
        for item in vendor_offers.get("items", [])
        if item["rfo_id"] == rfo_id
    ]

    response = templates.TemplateResponse(
        "rfo_detail.html",
        {
            "request": request,
            "rfo": rfo,
            "offers": offers,
            "vendor": vendor,
            "api_key": api_key,
        },
    )
    if api_key and api_key != request.cookies.get("api_key"):
        response.set_cookie("api_key", api_key, httponly=True)
    return response


@router.post("/rfos/{rfo_id}/offers")
async def dashboard_submit_offer(
    request: Request,
    rfo_id: int,
    price_amount: float = Form(...),
    currency: str = Form("USD"),
    delivery_eta_days: int = Form(...),
    warranty_months: int = Form(...),
    return_days: int = Form(...),
    stock: str | None = Form(None),
    api_key: str | None = Form(None),
    session: Session = Depends(get_session),
):
    vendor, resolved_key = await _get_vendor(request, form_api_key=api_key)
    if not vendor:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    payload = {
        "rfo_id": rfo_id,
        "price_amount": price_amount,
        "currency": currency,
        "delivery_eta_days": delivery_eta_days,
        "warranty_months": warranty_months,
        "return_days": return_days,
        "stock": bool(stock),
        "metadata": {},
    }

    transport = httpx.ASGITransport(app=request.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        api = UiApiClient(client)
        try:
            await api.submit_offer(resolved_key, payload)
        except httpx.HTTPStatusError as exc:
            try:
                error_detail = exc.response.json().get("detail")
            except ValueError:
                error_detail = exc.response.text
            error_message = error_detail or "Offer submission failed"
            try:
                rfo = await api.get_request(rfo_id)
            except httpx.HTTPStatusError as rfo_exc:
                if rfo_exc.response.status_code == 404:
                    raise HTTPException(status_code=404, detail="RFO not found") from rfo_exc
                raise
            vendor_offers = await api.list_vendor_offers(resolved_key)
            offers = [
                {
                    "id": item["offer_id"],
                    "price_amount": item["price_amount"],
                    "currency": item["currency"],
                    "delivery_eta_days": item["delivery_eta_days"],
                    "warranty_months": item["warranty_months"],
                    "return_days": item["return_days"],
                    "stock": item["stock"],
                }
                for item in vendor_offers.get("items", [])
                if item["rfo_id"] == rfo_id
            ]

            response = templates.TemplateResponse(
                "rfo_detail.html",
                {
                    "request": request,
                    "rfo": rfo,
                    "offers": offers,
                    "vendor": vendor,
                    "api_key": resolved_key,
                    "error": error_message,
                },
                status_code=exc.response.status_code,
            )
            if resolved_key and resolved_key != request.cookies.get("api_key"):
                response.set_cookie("api_key", resolved_key, httponly=True)
            return response

    response = RedirectResponse(url=f"/dashboard/rfos/{rfo_id}", status_code=303)
    if resolved_key and resolved_key != request.cookies.get("api_key"):
        response.set_cookie("api_key", resolved_key, httponly=True)
    return response


@router.get("/offers", response_class=HTMLResponse)
async def dashboard_offers(request: Request, session: Session = Depends(get_session)):
    vendor, api_key = await _get_vendor(request)
    if not vendor:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    transport = httpx.ASGITransport(app=request.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        api = UiApiClient(client)
        offer_payload = await api.list_vendor_offers(api_key)

    offer_rows = []
    for item in offer_payload.get("items", []):
        is_awarded = item.get("is_awarded") or item.get("status") == "awarded"
        offer_rows.append(
            {
                "offer": item,
                "request": item.get("request", {}),
                "status": "won" if is_awarded else "lost",
                "is_awarded": is_awarded,
            }
        )

    response = templates.TemplateResponse(
        "offers.html",
        {
            "request": request,
            "offers": offer_rows,
            "vendor": vendor,
            "api_key": api_key,
        },
    )
    if api_key and api_key != request.cookies.get("api_key"):
        response.set_cookie("api_key", api_key, httponly=True)
    return response


@router.get("/apis", response_class=HTMLResponse)
async def dashboard_api_list(request: Request, session: Session = Depends(get_session)):
    vendor, api_key = await _get_vendor(request)
    if not vendor:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    api_docs = list_api_docs()
    response = templates.TemplateResponse(
        "api_list.html",
        {"request": request, "api_docs": api_docs, "api_key": api_key},
    )
    if api_key and api_key != request.cookies.get("api_key"):
        response.set_cookie("api_key", api_key, httponly=True)
    return response


@router.get("/apis/{slug}", response_class=HTMLResponse)
async def dashboard_api_detail(
    request: Request,
    slug: str,
    session: Session = Depends(get_session),
):
    vendor, api_key = await _get_vendor(request)
    if not vendor:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    try:
        doc = get_api_doc(slug)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    response = templates.TemplateResponse(
        "api_detail.html",
        {"request": request, "doc": doc, "api_key": api_key},
    )
    if api_key and api_key != request.cookies.get("api_key"):
        response.set_cookie("api_key", api_key, httponly=True)
    return response
