from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from intentbid.app.db.models import PlanLimit, Subscription, UsageEvent


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


def record_usage(session: Session, vendor_id: int, event_type: str) -> UsageEvent:
    event = UsageEvent(vendor_id=vendor_id, event_type=event_type)
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
