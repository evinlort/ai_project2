from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from intentbid.app.db.models import AuditLog, Offer, RFO


def _sync_request_fields(
    constraints: dict | None,
    budget_max: float | None,
    delivery_deadline_days: int | None,
) -> tuple[dict, float | None, int | None]:
    merged_constraints = dict(constraints or {})

    resolved_budget_max = budget_max
    if resolved_budget_max is None:
        resolved_budget_max = merged_constraints.get("budget_max")
    else:
        merged_constraints["budget_max"] = resolved_budget_max

    resolved_deadline = delivery_deadline_days
    if resolved_deadline is None:
        resolved_deadline = merged_constraints.get("delivery_deadline_days")
    else:
        merged_constraints["delivery_deadline_days"] = resolved_deadline

    return merged_constraints, resolved_budget_max, resolved_deadline


def create_rfo(
    session: Session,
    category: str,
    constraints: dict,
    preferences: dict,
    buyer_id: int | None = None,
    title: str | None = None,
    summary: str | None = None,
    budget_max: float | None = None,
    currency: str | None = None,
    delivery_deadline_days: int | None = None,
    quantity: int | None = None,
    location: str | None = None,
    expires_at: datetime | None = None,
) -> RFO:
    merged_constraints, resolved_budget_max, resolved_deadline = _sync_request_fields(
        constraints, budget_max, delivery_deadline_days
    )

    rfo = RFO(
        category=category,
        constraints=merged_constraints,
        preferences=preferences,
        buyer_id=buyer_id,
        title=title,
        summary=summary,
        budget_max=resolved_budget_max,
        currency=currency,
        delivery_deadline_days=resolved_deadline,
        quantity=quantity,
        location=location,
        expires_at=expires_at,
    )
    session.add(rfo)
    session.commit()
    session.refresh(rfo)
    return rfo


def get_rfo_with_offers_count(session: Session, rfo_id: int) -> tuple[RFO | None, int]:
    rfo = session.get(RFO, rfo_id)
    if not rfo:
        return None, 0

    offers_count = session.exec(
        select(func.count(Offer.id)).where(Offer.rfo_id == rfo_id)
    ).one()
    return rfo, offers_count


def _log_rfo_action(
    session: Session,
    rfo_id: int,
    action: str,
    metadata: dict | None = None,
) -> None:
    audit = AuditLog(
        entity_type="rfo",
        entity_id=rfo_id,
        action=action,
        metadata_=metadata or {},
        created_at=datetime.now(timezone.utc),
    )
    session.add(audit)


def _transition_rfo(
    session: Session,
    rfo_id: int,
    from_statuses: set[str],
    to_status: str,
    action: str,
    reason: str | None = None,
) -> tuple[RFO | None, str | None]:
    rfo = session.get(RFO, rfo_id)
    if not rfo:
        return None, "not_found"
    if rfo.status not in from_statuses:
        return rfo, "invalid"

    rfo.status = to_status
    rfo.status_reason = reason
    session.add(rfo)
    metadata = {"reason": reason} if reason else {}
    _log_rfo_action(session, rfo_id, action, metadata)
    session.commit()
    session.refresh(rfo)
    return rfo, None


def close_rfo(session: Session, rfo_id: int, reason: str | None = None) -> tuple[RFO | None, str | None]:
    return _transition_rfo(session, rfo_id, {"OPEN"}, "CLOSED", "close", reason)


def award_rfo(
    session: Session,
    rfo_id: int,
    reason: str | None = None,
    offer_id: int | None = None,
) -> tuple[RFO | None, str | None]:
    rfo = session.get(RFO, rfo_id)
    if not rfo:
        return None, "not_found"
    if rfo.status not in {"CLOSED"}:
        return rfo, "invalid"

    if offer_id is not None:
        offer = session.get(Offer, offer_id)
        if not offer or offer.rfo_id != rfo_id:
            return rfo, "invalid_offer"
        offer.status = "awarded"
        offer.is_awarded = True
        session.add(offer)
        rfo.awarded_offer_id = offer_id

    rfo.status = "AWARDED"
    rfo.status_reason = reason
    session.add(rfo)

    metadata = {"reason": reason} if reason else {}
    if offer_id is not None:
        metadata["offer_id"] = offer_id
    _log_rfo_action(session, rfo_id, "award", metadata)

    session.commit()
    session.refresh(rfo)
    return rfo, None


def reopen_rfo(session: Session, rfo_id: int, reason: str | None = None) -> tuple[RFO | None, str | None]:
    return _transition_rfo(session, rfo_id, {"CLOSED"}, "OPEN", "reopen", reason)


def update_rfo_scoring_config(
    session: Session,
    rfo_id: int,
    scoring_version: str | None = None,
    weights: dict | None = None,
) -> RFO | None:
    rfo = session.get(RFO, rfo_id)
    if not rfo:
        return None
    if scoring_version:
        rfo.scoring_version = scoring_version
    if weights is not None:
        rfo.weights = weights
    session.add(rfo)
    session.commit()
    session.refresh(rfo)
    return rfo
