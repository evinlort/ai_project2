from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from intentbid.app.api.deps import require_buyer
from intentbid.app.core.schemas import (
    BestOffer,
    BuyerMeResponse,
    BuyerRankingResponse,
    BuyerRegisterRequest,
    BuyerRegisterResponse,
    OfferPublic,
    RFOListItem,
    RFOListResponse,
)
from intentbid.app.db.session import get_session
from intentbid.app.services.buyer_service import register_buyer
from intentbid.app.services.ranking_service import get_ranked_offers
from intentbid.app.services.rfo_service import list_rfos

router = APIRouter(prefix="/v1/buyers", tags=["buyers"])


@router.post("/register", response_model=BuyerRegisterResponse)
def register_buyer_route(
    payload: BuyerRegisterRequest,
    session: Session = Depends(get_session),
) -> BuyerRegisterResponse:
    buyer, api_key = register_buyer(session, payload.name)
    return BuyerRegisterResponse(buyer_id=buyer.id, api_key=api_key)


@router.get("/me", response_model=BuyerMeResponse)
def buyer_me(buyer=Depends(require_buyer)) -> BuyerMeResponse:
    return BuyerMeResponse(buyer_id=buyer.id, name=buyer.name)


@router.get("/rfo/{rfo_id}/ranking", response_model=BuyerRankingResponse)
def buyer_rfo_ranking(
    rfo_id: int,
    buyer=Depends(require_buyer),
    session: Session = Depends(get_session),
) -> BuyerRankingResponse:
    _ = buyer
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
                    unit_price=offer.unit_price,
                    currency=offer.currency,
                    delivery_eta_days=offer.delivery_eta_days,
                    lead_time_days=offer.lead_time_days,
                    available_qty=offer.available_qty,
                    shipping_cost=offer.shipping_cost,
                    tax_estimate=offer.tax_estimate,
                    condition=offer.condition,
                    warranty_months=offer.warranty_months,
                    return_days=offer.return_days,
                    stock=offer.stock,
                    traceability=offer.traceability or {},
                    valid_until=offer.valid_until,
                    metadata=offer.metadata_ or {},
                    created_at=offer.created_at,
                ),
            )
        )

    return BuyerRankingResponse(rfo_id=rfo.id, offers=offers)


@router.get("/rfos", response_model=RFOListResponse)
def buyer_rfo_list(
    status: str | None = Query(None),
    category: str | None = Query(None),
    budget_min: float | None = Query(None, ge=0),
    budget_max: float | None = Query(None, ge=0),
    deadline_max: int | None = Query(None, ge=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    buyer=Depends(require_buyer),
    session: Session = Depends(get_session),
) -> RFOListResponse:
    rfos, total = list_rfos(
        session,
        status=status,
        category=category,
        budget_min=budget_min,
        budget_max=budget_max,
        deadline_max=deadline_max,
        buyer_id=buyer.id,
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
