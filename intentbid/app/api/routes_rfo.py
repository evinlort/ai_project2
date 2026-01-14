from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from intentbid.app.api.deps import optional_buyer
from intentbid.app.core.schemas import (
    BestOffer,
    BestOffersResponse,
    OfferPublic,
    RFOCreate,
    RFOCreateResponse,
    RFOExplainResponse,
    RFOScoringUpdateRequest,
    RFOScoringUpdateResponse,
    RFOStatusUpdateRequest,
    RFOStatusUpdateResponse,
    RFODetailResponse,
)
from intentbid.app.db.session import get_session
from intentbid.app.services.ranking_service import get_best_offers, get_ranked_offers
from intentbid.app.services.rfo_service import (
    award_rfo,
    close_rfo,
    create_rfo,
    get_rfo_with_offers_count,
    reopen_rfo,
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
    )
    return RFOCreateResponse(rfo_id=rfo.id, status=rfo.status)


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
        constraints=rfo.constraints,
        preferences=rfo.preferences,
        status=rfo.status,
        created_at=rfo.created_at,
        offers_count=offers_count,
    )


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
    rfo, error = award_rfo(session, rfo_id, reason)
    if error == "not_found":
        raise HTTPException(status_code=404, detail="RFO not found")
    if error == "invalid":
        raise HTTPException(status_code=400, detail="Invalid RFO status transition")
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
