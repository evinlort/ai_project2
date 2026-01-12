from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from intentbid.app.api.deps import require_buyer
from intentbid.app.core.schemas import (
    BestOffer,
    BuyerMeResponse,
    BuyerRankingResponse,
    BuyerRegisterRequest,
    BuyerRegisterResponse,
    OfferPublic,
)
from intentbid.app.db.session import get_session
from intentbid.app.services.buyer_service import register_buyer
from intentbid.app.services.ranking_service import get_ranked_offers

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

    return BuyerRankingResponse(rfo_id=rfo.id, offers=offers)
