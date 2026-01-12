from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from intentbid.app.core.config import settings
from intentbid.app.core.schemas import OfferCreate
from intentbid.app.db.models import Offer
from intentbid.app.services.billing_service import (
    get_active_subscription,
    get_plan_limit,
    is_within_offer_limit,
    record_usage,
)
from intentbid.app.services.webhook_service import enqueue_event


def create_offer(session: Session, vendor_id: int, payload: OfferCreate) -> Offer:
    offer = Offer(
        rfo_id=payload.rfo_id,
        vendor_id=vendor_id,
        price_amount=payload.price_amount,
        currency=payload.currency,
        delivery_eta_days=payload.delivery_eta_days,
        warranty_months=payload.warranty_months,
        return_days=payload.return_days,
        stock=payload.stock,
        metadata_=payload.metadata,
    )
    session.add(offer)
    session.commit()
    session.refresh(offer)
    enqueue_event(
        session,
        vendor_id=vendor_id,
        event_type="offer.created",
        payload={
            "offer_id": offer.id,
            "rfo_id": offer.rfo_id,
            "vendor_id": vendor_id,
        },
    )
    record_usage(session, vendor_id=vendor_id, event_type="offer.created")
    return offer


def validate_offer_submission(
    session: Session,
    vendor_id: int,
    payload: OfferCreate,
) -> tuple[bool, int | None, str | None]:
    subscription = get_active_subscription(session, vendor_id)
    if subscription:
        plan = get_plan_limit(session, subscription.plan_code)
        if plan and not is_within_offer_limit(session, vendor_id, plan.max_offers_per_month):
            return False, 429, "Plan limit exceeded"

    if payload.price_amount <= 0:
        return False, 400, "Price must be positive"
    if payload.delivery_eta_days <= 0:
        return False, 400, "Delivery ETA must be positive"
    if payload.warranty_months < 0 or payload.return_days < 0:
        return False, 400, "Warranty and return days must be non-negative"

    offers_count = session.exec(
        select(func.count(Offer.id)).where(
            Offer.vendor_id == vendor_id,
            Offer.rfo_id == payload.rfo_id,
        )
    ).one()
    if offers_count >= settings.max_offers_per_vendor_rfo:
        return False, 429, "Offer limit reached for this RFO"

    last_offer = session.exec(
        select(Offer)
        .where(
            Offer.vendor_id == vendor_id,
            Offer.rfo_id == payload.rfo_id,
        )
        .order_by(Offer.created_at.desc())
    ).first()
    if last_offer and settings.offer_cooldown_seconds > 0:
        last_created_at = last_offer.created_at
        if last_created_at.tzinfo is None:
            last_created_at = last_created_at.replace(tzinfo=timezone.utc)
        cooldown_until = last_created_at + timedelta(seconds=settings.offer_cooldown_seconds)
        if datetime.now(timezone.utc) < cooldown_until:
            return False, 429, "Offer cooldown active"

    return True, None, None
