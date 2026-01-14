from pathlib import Path

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from intentbid.app.db.session import get_session
from intentbid.app.services.buyer_service import get_buyer_by_api_key
from intentbid.app.services.ranking_service import get_best_offers, get_ranked_offers
from intentbid.app.services.rfo_service import create_rfo, get_rfo_with_offers_count

router = APIRouter(prefix="/buyer", tags=["buyer-dashboard"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _resolve_buyer_key(request: Request, form_api_key: str | None = None) -> str | None:
    return (
        form_api_key
        or request.query_params.get("buyer_api_key")
        or request.cookies.get("buyer_api_key")
    )


def _get_buyer(session: Session, request: Request, form_api_key: str | None = None):
    api_key = _resolve_buyer_key(request, form_api_key)
    if not api_key:
        return None, None

    buyer = get_buyer_by_api_key(session, api_key)
    return buyer, api_key


@router.get("/rfos/new", response_class=HTMLResponse)
def buyer_rfo_create_page(request: Request):
    buyer_api_key = request.cookies.get("buyer_api_key")
    return templates.TemplateResponse(
        "buyer/rfo_new.html",
        {"request": request, "buyer_api_key": buyer_api_key},
    )


@router.post("/rfos/new")
def buyer_rfo_create_submit(
    request: Request,
    category: str = Form(...),
    budget_max: float = Form(...),
    size: int | None = Form(None),
    delivery_deadline_days: int = Form(...),
    w_price: float = Form(...),
    w_delivery: float = Form(...),
    w_warranty: float = Form(...),
    session: Session = Depends(get_session),
):
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
    rfo = create_rfo(session, category, constraints, preferences, buyer_id=None)
    return RedirectResponse(url=f"/buyer/rfos/check?rfo_id={rfo.id}", status_code=303)


@router.get("/rfos/check", response_class=HTMLResponse)
def buyer_rfo_check(
    request: Request,
    rfo_id: int | None = Query(None, ge=1),
    session: Session = Depends(get_session),
):
    buyer_api_key = _resolve_buyer_key(request)
    rfo = None
    offers_count = 0
    error = None

    if rfo_id is not None:
        rfo, offers_count = get_rfo_with_offers_count(session, rfo_id)
        if not rfo:
            error = "RFO not found"

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
def buyer_best_offers(
    request: Request,
    rfo_id: int | None = Query(None, ge=1),
    top_k: int = Query(3, ge=1, le=50),
    session: Session = Depends(get_session),
):
    rfo = None
    offer_rows = []
    error = None

    if rfo_id is not None:
        rfo, scored_offers = get_best_offers(session, rfo_id, top_k)
        if not rfo:
            error = "RFO not found"
        else:
            offer_rows = [
                {"offer": offer, "score": score, "explain": explain}
                for offer, score, explain in scored_offers
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
def buyer_scoring(
    request: Request,
    rfo_id: int | None = Query(None, ge=1),
    session: Session = Depends(get_session),
):
    buyer_api_key = _resolve_buyer_key(request)
    buyer = get_buyer_by_api_key(session, buyer_api_key) if buyer_api_key else None
    rfo = None
    offer_rows = []
    error = None

    if rfo_id is not None:
        if not buyer_api_key:
            error = "Add your buyer API key to view scoring."
        elif not buyer:
            error = "Invalid buyer API key."
        else:
            rfo, scored_offers = get_ranked_offers(session, rfo_id)
            if not rfo:
                error = "RFO not found"
            else:
                offer_rows = [
                    {"offer": offer, "score": score, "explain": explain}
                    for offer, score, explain in scored_offers
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
