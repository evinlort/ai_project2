from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from intentbid.app.db.models import (
    BuyerSubscription,
    BuyerUsageEvent,
    PlanLimit,
    Subscription,
    UsageEvent,
)


def get_active_subscription(session: Session, vendor_id: int) -> Subscription | None:
    return session.exec(
        select(Subscription).where(
            Subscription.vendor_id == vendor_id,
            Subscription.status == "active",
        )
    ).first()


def get_plan_limit(session: Session, plan_code: str) -> PlanLimit | None:
    return session.exec(
        select(PlanLimit).where(PlanLimit.plan_code == plan_code)
    ).first()


def get_active_buyer_subscription(session: Session, buyer_id: int) -> BuyerSubscription | None:
    return session.exec(
        select(BuyerSubscription).where(
            BuyerSubscription.buyer_id == buyer_id,
            BuyerSubscription.status == "active",
        )
    ).first()


def record_usage(session: Session, vendor_id: int, event_type: str) -> UsageEvent:
    event = UsageEvent(vendor_id=vendor_id, event_type=event_type)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def record_buyer_usage(session: Session, buyer_id: int, event_type: str) -> BuyerUsageEvent:
    event = BuyerUsageEvent(buyer_id=buyer_id, event_type=event_type)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def _month_start(now: datetime) -> datetime:
    return datetime(now.year, now.month, 1, tzinfo=timezone.utc)


def is_within_offer_limit(session: Session, vendor_id: int, limit: int) -> bool:
    now = datetime.now(timezone.utc)
    month_start = _month_start(now)
    count = session.exec(
        select(func.count(UsageEvent.id)).where(
            UsageEvent.vendor_id == vendor_id,
            UsageEvent.event_type == "offer.created",
            UsageEvent.created_at >= month_start,
        )
    ).one()
    return count < limit


def is_within_buyer_rfo_limit(session: Session, buyer_id: int, limit: int) -> bool:
    now = datetime.now(timezone.utc)
    month_start = _month_start(now)
    count = session.exec(
        select(func.count(BuyerUsageEvent.id)).where(
            BuyerUsageEvent.buyer_id == buyer_id,
            BuyerUsageEvent.event_type == "rfo.created",
            BuyerUsageEvent.created_at >= month_start,
        )
    ).one()
    return count < limit


def is_within_buyer_award_limit(session: Session, buyer_id: int, limit: int) -> bool:
    now = datetime.now(timezone.utc)
    month_start = _month_start(now)
    count = session.exec(
        select(func.count(BuyerUsageEvent.id)).where(
            BuyerUsageEvent.buyer_id == buyer_id,
            BuyerUsageEvent.event_type == "rfo.awarded",
            BuyerUsageEvent.created_at >= month_start,
        )
    ).one()
    return count < limit


def get_offer_usage_summary(session: Session, vendor_id: int) -> dict | None:
    subscription = get_active_subscription(session, vendor_id)
    if not subscription:
        return None

    now = datetime.now(timezone.utc)
    month_start = _month_start(now)
    used = session.exec(
        select(func.count(UsageEvent.id)).where(
            UsageEvent.vendor_id == vendor_id,
            UsageEvent.event_type == "offer.created",
            UsageEvent.created_at >= month_start,
        )
    ).one()

    plan = get_plan_limit(session, subscription.plan_code)
    limit = plan.max_offers_per_month if plan else None
    return {
        "plan_code": subscription.plan_code,
        "used": used,
        "limit": limit,
    }
