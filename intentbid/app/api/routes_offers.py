from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from intentbid.app.api.deps import require_vendor
from intentbid.app.core.config import settings
from intentbid.app.core.schemas import (
    OfferCreate,
    OfferCreateResponse,
    OfferUpdateRequest,
    OfferUpdateResponse,
    PartCategory,
)
from intentbid.app.db.models import IdempotencyKey, Offer, OfferRevision, RFO
from intentbid.app.db.session import get_session
from intentbid.app.services.offer_service import create_offer, validate_offer_submission

router = APIRouter(prefix="/v1/offers", tags=["offers"])
HARDWARE_CATEGORIES = {category.value for category in PartCategory}


@router.post("", response_model=OfferCreateResponse)
def submit_offer(
    payload: OfferCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: Session = Depends(get_session),
    vendor=Depends(require_vendor),
) -> OfferCreateResponse:
    if idempotency_key:
        cached = session.exec(
            select(IdempotencyKey).where(
                IdempotencyKey.key == idempotency_key,
                IdempotencyKey.endpoint == "POST /v1/offers",
            )
        ).first()
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response_body)

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
    response_body = {"offer_id": offer.id}
    if idempotency_key:
        session.add(
            IdempotencyKey(
                key=idempotency_key,
                endpoint="POST /v1/offers",
                status_code=200,
                response_body=response_body,
            )
        )
        session.commit()
    return OfferCreateResponse(**response_body)


@router.patch("/{offer_id}", response_model=OfferUpdateResponse)
def update_offer(
    offer_id: int,
    payload: OfferUpdateRequest,
    session: Session = Depends(get_session),
    vendor=Depends(require_vendor),
) -> OfferUpdateResponse:
    offer = session.get(Offer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.vendor_id != vendor.id:
        raise HTTPException(status_code=403, detail="Offer does not belong to vendor")

    rfo = session.get(RFO, offer.rfo_id)
    if not rfo or rfo.status != "OPEN":
        raise HTTPException(status_code=400, detail="RFO must be OPEN to update offers")

    now = datetime.now(timezone.utc)
    if offer.valid_until is not None:
        valid_until = offer.valid_until
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)
        if now > valid_until:
            raise HTTPException(status_code=400, detail="Offer validity window has expired")

    last_update = offer.updated_at or offer.created_at
    if last_update.tzinfo is None:
        last_update = last_update.replace(tzinfo=timezone.utc)
    if settings.offer_cooldown_seconds > 0:
        cooldown_until = last_update + timedelta(seconds=settings.offer_cooldown_seconds)
        if now < cooldown_until:
            raise HTTPException(status_code=429, detail="Offer update cooldown active")

    updates = payload.model_dump(exclude_unset=True)
    if "price_amount" in updates and updates["price_amount"] <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive")
    if "unit_price" in updates and updates["unit_price"] <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive")
    if "delivery_eta_days" in updates and updates["delivery_eta_days"] <= 0:
        raise HTTPException(status_code=400, detail="Delivery ETA must be positive")
    if "lead_time_days" in updates and updates["lead_time_days"] <= 0:
        raise HTTPException(status_code=400, detail="Lead time must be positive")
    if "available_qty" in updates and updates["available_qty"] <= 0:
        raise HTTPException(status_code=400, detail="Available quantity must be positive")
    if "shipping_cost" in updates and updates["shipping_cost"] < 0:
        raise HTTPException(status_code=400, detail="Shipping cost must be non-negative")
    if "tax_estimate" in updates and updates["tax_estimate"] < 0:
        raise HTTPException(status_code=400, detail="Tax estimate must be non-negative")
    if "warranty_months" in updates and updates["warranty_months"] < 0:
        raise HTTPException(status_code=400, detail="Warranty must be non-negative")
    if "return_days" in updates and updates["return_days"] < 0:
        raise HTTPException(status_code=400, detail="Return days must be non-negative")

    if "unit_price" in updates and "price_amount" not in updates:
        updates["price_amount"] = updates["unit_price"]
    if "price_amount" in updates and "unit_price" not in updates:
        updates["unit_price"] = updates["price_amount"]
    if "lead_time_days" in updates and "delivery_eta_days" not in updates:
        updates["delivery_eta_days"] = updates["lead_time_days"]
    if "delivery_eta_days" in updates and "lead_time_days" not in updates:
        updates["lead_time_days"] = updates["delivery_eta_days"]

    revision = OfferRevision(
        offer_id=offer.id,
        offer_version=offer.offer_version,
        snapshot=offer.model_dump(),
    )
    session.add(revision)

    for field, value in updates.items():
        setattr(offer, field, value)
    offer.offer_version += 1
    offer.updated_at = now
    session.add(offer)
    session.commit()
    session.refresh(offer)

    return OfferUpdateResponse(offer_id=offer.id, offer_version=offer.offer_version)
