from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from intentbid.app.core.schemas import (
    BestOffer,
    BestOffersResponse,
    OfferPublic,
    RFOCreate,
    RFOCreateResponse,
    RFODetailResponse,
)
from intentbid.app.db.session import get_session
from intentbid.app.services.ranking_service import get_best_offers
from intentbid.app.services.rfo_service import create_rfo, get_rfo_with_offers_count

router = APIRouter(prefix="/v1/rfo", tags=["rfo"])


@router.post("", response_model=RFOCreateResponse)
def create_rfo_route(
    payload: RFOCreate,
    session: Session = Depends(get_session),
) -> RFOCreateResponse:
    rfo = create_rfo(session, payload.category, payload.constraints, payload.preferences)
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
