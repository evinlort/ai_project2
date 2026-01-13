from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from intentbid.app.core.schemas import OfferCreate
from intentbid.app.core.scoring import score_offer
from intentbid.app.db.models import Offer, RFO
from intentbid.app.db.session import get_session
from intentbid.app.services.offer_service import create_offer
from intentbid.app.services.vendor_service import get_vendor_by_api_key
from intentbid.app.api.api_docs import get_api_doc, list_api_docs

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _resolve_api_key(request: Request, form_api_key: str | None = None) -> str | None:
    return form_api_key or request.query_params.get("api_key") or request.cookies.get("api_key")


def _get_vendor(session: Session, request: Request, form_api_key: str | None = None):
    api_key = _resolve_api_key(request, form_api_key)
    if not api_key:
        return None, None

    vendor = get_vendor_by_api_key(session, api_key)
    return vendor, api_key


@router.get("/login", response_class=HTMLResponse)
def dashboard_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
def dashboard_login_submit(
    request: Request,
    api_key: str = Form(...),
    session: Session = Depends(get_session),
):
    vendor = get_vendor_by_api_key(session, api_key)
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
def dashboard_rfos(request: Request, session: Session = Depends(get_session)):
    vendor, api_key = _get_vendor(session, request)
    if not vendor:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    rfos = session.exec(
        select(RFO).where(RFO.status == "OPEN").order_by(RFO.created_at.desc())
    ).all()

    response = templates.TemplateResponse(
        "rfos.html",
        {"request": request, "rfos": rfos, "vendor": vendor, "api_key": api_key},
    )
    if api_key and api_key != request.cookies.get("api_key"):
        response.set_cookie("api_key", api_key, httponly=True)
    return response


@router.get("/rfos/{rfo_id}", response_class=HTMLResponse)
def dashboard_rfo_detail(
    request: Request,
    rfo_id: int,
    session: Session = Depends(get_session),
):
    vendor, api_key = _get_vendor(session, request)
    if not vendor:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    rfo = session.get(RFO, rfo_id)
    if not rfo:
        raise HTTPException(status_code=404, detail="RFO not found")

    offers = session.exec(select(Offer).where(Offer.rfo_id == rfo_id)).all()

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
def dashboard_submit_offer(
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
    vendor, resolved_key = _get_vendor(session, request, form_api_key=api_key)
    if not vendor:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    rfo = session.get(RFO, rfo_id)
    if not rfo:
        raise HTTPException(status_code=404, detail="RFO not found")
    if rfo.status != "OPEN":
        return RedirectResponse(url=f"/dashboard/rfos/{rfo_id}", status_code=303)

    payload = OfferCreate(
        rfo_id=rfo_id,
        price_amount=price_amount,
        currency=currency,
        delivery_eta_days=delivery_eta_days,
        warranty_months=warranty_months,
        return_days=return_days,
        stock=bool(stock),
        metadata={},
    )
    create_offer(session, vendor.id, payload)

    response = RedirectResponse(url=f"/dashboard/rfos/{rfo_id}", status_code=303)
    if resolved_key and resolved_key != request.cookies.get("api_key"):
        response.set_cookie("api_key", resolved_key, httponly=True)
    return response


@router.get("/offers", response_class=HTMLResponse)
def dashboard_offers(request: Request, session: Session = Depends(get_session)):
    vendor, api_key = _get_vendor(session, request)
    if not vendor:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    offers = session.exec(select(Offer).where(Offer.vendor_id == vendor.id)).all()
    rfo_ids = {offer.rfo_id for offer in offers}
    rfos = {
        rfo.id: rfo
        for rfo in session.exec(select(RFO).where(RFO.id.in_(rfo_ids))).all()
    }

    offer_rows = []
    best_scores = {}
    for offer in offers:
        rfo = rfos.get(offer.rfo_id)
        if not rfo:
            continue
        score, _ = score_offer(offer, rfo)
        best_scores[offer.rfo_id] = max(best_scores.get(offer.rfo_id, 0), score)
        offer_rows.append({"offer": offer, "score": score, "rfo": rfo})

    for row in offer_rows:
        row["status"] = "won" if row["score"] == best_scores.get(row["rfo"].id, 0) else "lost"

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
def dashboard_api_list(request: Request, session: Session = Depends(get_session)):
    vendor, api_key = _get_vendor(session, request)
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
def dashboard_api_detail(
    request: Request,
    slug: str,
    session: Session = Depends(get_session),
):
    vendor, api_key = _get_vendor(session, request)
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
