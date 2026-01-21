from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from intentbid.app.api.deps import optional_buyer, require_buyer
from intentbid.app.core.schemas import (
    BestOffer,
    BestOffersResponse,
    OfferPublic,
    RFOCreate,
    RFOCreateResponse,
    RFOExplainResponse,
    RFOListItem,
    RFOListResponse,
    RFOOffersResponse,
    RFOScoringUpdateRequest,
    RFOScoringUpdateResponse,
    RFOUpdateRequest,
    RFOStatusUpdateRequest,
    RFOStatusUpdateResponse,
    RFODetailResponse,
)
from intentbid.app.db.models import Offer, RFO
from intentbid.app.db.session import get_session
from intentbid.app.services.ranking_service import get_best_offers, get_ranked_offers
from intentbid.app.services.rfo_service import (
    award_rfo,
    close_rfo,
    create_rfo,
    get_rfo_with_offers_count,
    list_rfos,
    reopen_rfo,
    update_rfo,
    update_rfo_scoring_config,
)

router = APIRouter(prefix="/v1/rfo", tags=["rfo"])


@router.post("", response_model=RFOCreateResponse)
def create_rfo_route(
    payload: RFOCreate,
    buyer=Depends(optional_buyer),
    session: Session = Depends(get_session),
) -> RFOCreateResponse:
    buyer_id = buyer.id if buyer else None
    rfo = create_rfo(
        session,
        payload.category,
        payload.constraints,
        payload.preferences,
        buyer_id=buyer_id,
        title=payload.title,
        summary=payload.summary,
        budget_max=payload.budget_max,
        currency=payload.currency,
        delivery_deadline_days=payload.delivery_deadline_days,
        quantity=payload.quantity,
        location=payload.location,
        expires_at=payload.expires_at,
    )
    return RFOCreateResponse(rfo_id=rfo.id, status=rfo.status)


@router.get("", response_model=RFOListResponse)
def list_rfos_route(
    status: str | None = Query(None),
    category: str | None = Query(None),
    budget_min: float | None = Query(None, ge=0),
    budget_max: float | None = Query(None, ge=0),
    deadline_max: int | None = Query(None, ge=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
) -> RFOListResponse:
    rfos, total = list_rfos(
        session,
        status=status,
        category=category,
        budget_min=budget_min,
        budget_max=budget_max,
        deadline_max=deadline_max,
        limit=limit,
        offset=offset,
    )

    items = [
        RFOListItem(
            id=rfo.id,
            category=rfo.category,
            title=rfo.title,
            summary=rfo.summary,
            budget_max=rfo.budget_max,
            currency=rfo.currency,
            delivery_deadline_days=rfo.delivery_deadline_days,
            quantity=rfo.quantity,
            location=rfo.location,
            expires_at=rfo.expires_at,
            status=rfo.status,
            created_at=rfo.created_at,
        )
        for rfo in rfos
    ]

    return RFOListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{rfo_id}", response_model=RFODetailResponse)
def get_rfo_route(
    rfo_id: int,
    session: Session = Depends(get_session),
) -> RFODetailResponse:
    rfo, offers_count = get_rfo_with_offers_count(session, rfo_id)
    if not rfo:
        raise HTTPException(status_code=404, detail="RFO not found")

    return RFODetailResponse(
        id=rfo.id,
        category=rfo.category,
        title=rfo.title,
        summary=rfo.summary,
        budget_max=rfo.budget_max,
        currency=rfo.currency,
        delivery_deadline_days=rfo.delivery_deadline_days,
        quantity=rfo.quantity,
        location=rfo.location,
        expires_at=rfo.expires_at,
        constraints=rfo.constraints,
        preferences=rfo.preferences,
        status=rfo.status,
        created_at=rfo.created_at,
        offers_count=offers_count,
    )


@router.patch("/{rfo_id}", response_model=RFODetailResponse)
def update_rfo_route(
    rfo_id: int,
    payload: RFOUpdateRequest,
    buyer=Depends(require_buyer),
    session: Session = Depends(get_session),
) -> RFODetailResponse:
    updates = payload.model_dump(exclude_unset=True)
    rfo, error = update_rfo(session, rfo_id, buyer.id, updates)
    if error == "not_found":
        raise HTTPException(status_code=404, detail="RFO not found")
    if error == "forbidden":
        raise HTTPException(status_code=403, detail="Buyer does not own this RFO")
    if error == "invalid":
        raise HTTPException(status_code=400, detail="RFO must be OPEN to update")

    rfo, offers_count = get_rfo_with_offers_count(session, rfo_id)
    if not rfo:
        raise HTTPException(status_code=404, detail="RFO not found")

    return RFODetailResponse(
        id=rfo.id,
        category=rfo.category,
        title=rfo.title,
        summary=rfo.summary,
        budget_max=rfo.budget_max,
        currency=rfo.currency,
        delivery_deadline_days=rfo.delivery_deadline_days,
        quantity=rfo.quantity,
        location=rfo.location,
        expires_at=rfo.expires_at,
        constraints=rfo.constraints,
        preferences=rfo.preferences,
        status=rfo.status,
        created_at=rfo.created_at,
        offers_count=offers_count,
    )


@router.get("/{rfo_id}/offers", response_model=RFOOffersResponse)
def get_rfo_offers(
    rfo_id: int,
    buyer=Depends(require_buyer),
    session: Session = Depends(get_session),
) -> RFOOffersResponse:
    rfo = session.get(RFO, rfo_id)
    if not rfo:
        raise HTTPException(status_code=404, detail="RFO not found")
    if rfo.buyer_id != buyer.id:
        raise HTTPException(status_code=403, detail="Buyer does not own this RFO")

    offers = session.exec(select(Offer).where(Offer.rfo_id == rfo_id)).all()
    items = [
        OfferPublic(
            id=offer.id,
            rfo_id=offer.rfo_id,
            vendor_id=offer.vendor_id,
            price_amount=offer.price_amount,
            currency=offer.currency,
            delivery_eta_days=offer.delivery_eta_days,
            warranty_months=offer.warranty_months,
            return_days=offer.return_days,
            stock=offer.stock,
            metadata=offer.metadata_ or {},
            created_at=offer.created_at,
        )
        for offer in offers
    ]
    return RFOOffersResponse(rfo_id=rfo.id, offers=items)


@router.get("/{rfo_id}/best", response_model=BestOffersResponse)
def get_best_offers_route(
    rfo_id: int,
    top_k: int = Query(3, ge=1, le=50),
    session: Session = Depends(get_session),
) -> BestOffersResponse:
    rfo, scored_offers = get_best_offers(session, rfo_id, top_k)
    if not rfo:
        raise HTTPException(status_code=404, detail="RFO not found")

    top_offers = []
    for offer, score, explain in scored_offers:
        top_offers.append(
            BestOffer(
                offer_id=offer.id,
                vendor_id=offer.vendor_id,
                score=score,
                explain=explain,
                offer=OfferPublic(
                    id=offer.id,
                    rfo_id=offer.rfo_id,
                    vendor_id=offer.vendor_id,
                    price_amount=offer.price_amount,
                    currency=offer.currency,
                    delivery_eta_days=offer.delivery_eta_days,
                    warranty_months=offer.warranty_months,
                    return_days=offer.return_days,
                    stock=offer.stock,
                    metadata=offer.metadata_ or {},
                    created_at=offer.created_at,
                ),
            )
        )

    return BestOffersResponse(rfo_id=rfo.id, top_offers=top_offers)


@router.get("/{rfo_id}/ranking/explain", response_model=RFOExplainResponse)
def get_rfo_ranking_explain(
    rfo_id: int,
    session: Session = Depends(get_session),
) -> RFOExplainResponse:
    rfo, scored_offers = get_ranked_offers(session, rfo_id)
    if not rfo:
        raise HTTPException(status_code=404, detail="RFO not found")

    offers = []
    for offer, score, explain in scored_offers:
        offers.append(
            BestOffer(
                offer_id=offer.id,
                vendor_id=offer.vendor_id,
                score=score,
                explain=explain,
                offer=OfferPublic(
                    id=offer.id,
                    rfo_id=offer.rfo_id,
                    vendor_id=offer.vendor_id,
                    price_amount=offer.price_amount,
                    currency=offer.currency,
                    delivery_eta_days=offer.delivery_eta_days,
                    warranty_months=offer.warranty_months,
                    return_days=offer.return_days,
                    stock=offer.stock,
                    metadata=offer.metadata_ or {},
                    created_at=offer.created_at,
                ),
            )
        )

    return RFOExplainResponse(
        rfo_id=rfo.id,
        scoring_version=rfo.scoring_version,
        offers=offers,
    )


@router.post("/{rfo_id}/scoring", response_model=RFOScoringUpdateResponse)
def update_rfo_scoring(
    rfo_id: int,
    payload: RFOScoringUpdateRequest,
    session: Session = Depends(get_session),
) -> RFOScoringUpdateResponse:
    rfo = update_rfo_scoring_config(
        session,
        rfo_id,
        scoring_version=payload.scoring_version,
        weights=payload.weights,
    )
    if not rfo:
        raise HTTPException(status_code=404, detail="RFO not found")
    return RFOScoringUpdateResponse(
        rfo_id=rfo.id,
        scoring_version=rfo.scoring_version,
        weights=rfo.weights,
    )


@router.post("/{rfo_id}/close", response_model=RFOStatusUpdateResponse)
def close_rfo_route(
    rfo_id: int,
    payload: RFOStatusUpdateRequest | None = None,
    session: Session = Depends(get_session),
) -> RFOStatusUpdateResponse:
    reason = payload.reason if payload else None
    rfo, error = close_rfo(session, rfo_id, reason)
    if error == "not_found":
        raise HTTPException(status_code=404, detail="RFO not found")
    if error == "invalid":
        raise HTTPException(status_code=400, detail="Invalid RFO status transition")
    return RFOStatusUpdateResponse(rfo_id=rfo.id, status=rfo.status, reason=rfo.status_reason)


@router.post("/{rfo_id}/award", response_model=RFOStatusUpdateResponse)
def award_rfo_route(
    rfo_id: int,
    payload: RFOStatusUpdateRequest | None = None,
    session: Session = Depends(get_session),
) -> RFOStatusUpdateResponse:
    reason = payload.reason if payload else None
    offer_id = payload.offer_id if payload else None
    rfo, error = award_rfo(session, rfo_id, reason, offer_id=offer_id)
    if error == "not_found":
        raise HTTPException(status_code=404, detail="RFO not found")
    if error == "invalid":
        raise HTTPException(status_code=400, detail="Invalid RFO status transition")
    if error == "invalid_offer":
        raise HTTPException(status_code=400, detail="Invalid offer for this RFO")
    return RFOStatusUpdateResponse(rfo_id=rfo.id, status=rfo.status, reason=rfo.status_reason)


@router.post("/{rfo_id}/reopen", response_model=RFOStatusUpdateResponse)
def reopen_rfo_route(
    rfo_id: int,
    payload: RFOStatusUpdateRequest | None = None,
    session: Session = Depends(get_session),
) -> RFOStatusUpdateResponse:
    reason = payload.reason if payload else None
    rfo, error = reopen_rfo(session, rfo_id, reason)
    if error == "not_found":
        raise HTTPException(status_code=404, detail="RFO not found")
    if error == "invalid":
        raise HTTPException(status_code=400, detail="Invalid RFO status transition")
    return RFOStatusUpdateResponse(rfo_id=rfo.id, status=rfo.status, reason=rfo.status_reason)
