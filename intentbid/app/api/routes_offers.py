from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from intentbid.app.api.deps import require_vendor
from intentbid.app.core.schemas import OfferCreate, OfferCreateResponse
from intentbid.app.db.models import RFO
from intentbid.app.db.session import get_session
from intentbid.app.services.offer_service import create_offer, validate_offer_submission

router = APIRouter(prefix="/v1/offers", tags=["offers"])


@router.post("", response_model=OfferCreateResponse)
def submit_offer(
    payload: OfferCreate,
    session: Session = Depends(get_session),
    vendor=Depends(require_vendor),
) -> OfferCreateResponse:
    rfo = session.get(RFO, payload.rfo_id)
    if not rfo:
        raise HTTPException(status_code=404, detail="RFO not found")
    if rfo.status != "OPEN":
        raise HTTPException(status_code=400, detail="RFO is closed")

    ok, status_code, detail = validate_offer_submission(session, vendor.id, payload)
    if not ok:
        raise HTTPException(status_code=status_code or 400, detail=detail or "Invalid offer")

    offer = create_offer(session, vendor.id, payload)
    return OfferCreateResponse(offer_id=offer.id)
