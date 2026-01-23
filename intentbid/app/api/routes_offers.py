from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from intentbid.app.api.deps import require_vendor
from intentbid.app.core.config import settings
from intentbid.app.core.schemas import OfferCreate, OfferCreateResponse, PartCategory
from intentbid.app.db.models import RFO
from intentbid.app.db.session import get_session
from intentbid.app.services.offer_service import create_offer, validate_offer_submission

router = APIRouter(prefix="/v1/offers", tags=["offers"])
HARDWARE_CATEGORIES = {category.value for category in PartCategory}


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
    if (
        settings.require_verified_vendors_for_hardware
        and rfo.category in HARDWARE_CATEGORIES
        and vendor.verification_status != "VERIFIED"
    ):
        raise HTTPException(status_code=403, detail="Vendor verification required")

    ok, status_code, detail = validate_offer_submission(session, vendor.id, payload)
    if not ok:
        raise HTTPException(status_code=status_code or 400, detail=detail or "Invalid offer")

    offer = create_offer(session, vendor.id, payload)
    return OfferCreateResponse(offer_id=offer.id)
