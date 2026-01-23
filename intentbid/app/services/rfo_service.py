from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from intentbid.app.db.models import AuditLog, Offer, RFO, Vendor
from intentbid.app.services.webhook_service import enqueue_event


def _sync_request_fields(
    constraints: dict | None,
    budget_max: float | None,
    delivery_deadline_days: int | None,
    currency: str | None,
) -> tuple[dict, float | None, int | None, str | None]:
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

    resolved_currency = currency
    if resolved_currency is None:
        resolved_currency = merged_constraints.get("currency")
    else:
        merged_constraints["currency"] = resolved_currency

    return merged_constraints, resolved_budget_max, resolved_deadline, resolved_currency


def _enqueue_rfo_event(
    session: Session,
    event_type: str,
    rfo: RFO,
    offer_id: int | None = None,
) -> None:
    vendor_ids = session.exec(select(Vendor.id)).all()
    payload = {
        "rfo_id": rfo.id,
        "status": rfo.status,
        "quote_deadline_hours": rfo.quote_deadline_hours,
    }
    if offer_id is not None:
        payload["offer_id"] = offer_id

    for vendor_id in vendor_ids:
        enqueue_event(session, vendor_id=vendor_id, event_type=event_type, payload=payload)


def create_rfo(
    session: Session,
    category: str,
    constraints: dict,
    preferences: dict,
    line_items: list[dict] | None = None,
    compliance: dict | None = None,
    scoring_profile: str | None = None,
    quote_deadline_hours: int | None = None,
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
    merged_constraints, resolved_budget_max, resolved_deadline, resolved_currency = _sync_request_fields(
        constraints, budget_max, delivery_deadline_days, currency
    )

    rfo = RFO(
        category=category,
        constraints=merged_constraints,
        preferences=preferences,
        line_items=line_items or [],
        compliance=compliance or {},
        scoring_profile=scoring_profile,
        quote_deadline_hours=quote_deadline_hours,
        buyer_id=buyer_id,
        title=title,
        summary=summary,
        budget_max=resolved_budget_max,
        currency=resolved_currency,
        delivery_deadline_days=resolved_deadline,
        quantity=quantity,
        location=location,
        expires_at=expires_at,
    )
    session.add(rfo)
    session.commit()
    session.refresh(rfo)
    _enqueue_rfo_event(session, "rfo.created", rfo)
    return rfo


def get_rfo_with_offers_count(session: Session, rfo_id: int) -> tuple[RFO | None, int]:
    rfo = session.get(RFO, rfo_id)
    if not rfo:
        return None, 0

    offers_count = session.exec(
        select(func.count(Offer.id)).where(Offer.rfo_id == rfo_id)
    ).one()
    return rfo, offers_count


def list_rfos(
    session: Session,
    status: str | None = None,
    category: str | None = None,
    budget_min: float | None = None,
    budget_max: float | None = None,
    deadline_max: int | None = None,
    buyer_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[RFO], int]:
    query = select(RFO)
    if buyer_id is not None:
        query = query.where(RFO.buyer_id == buyer_id)
    if status:
        query = query.where(RFO.status == status)
    if category:
        query = query.where(RFO.category == category)
    if budget_min is not None:
        query = query.where(RFO.budget_max >= budget_min)
    if budget_max is not None:
        query = query.where(RFO.budget_max <= budget_max)
    if deadline_max is not None:
        query = query.where(RFO.delivery_deadline_days <= deadline_max)

    total = session.exec(select(func.count()).select_from(query.subquery())).one()
    items = session.exec(
        query.order_by(RFO.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return items, total


def _log_rfo_action(
    session: Session,
    rfo_id: int,
    action: str,
    metadata: dict | None = None,
    buyer_id: int | None = None,
) -> None:
    resolved_metadata = dict(metadata or {})
    if buyer_id is not None:
        resolved_metadata["buyer_id"] = buyer_id
    audit = AuditLog(
        entity_type="rfo",
        entity_id=rfo_id,
        action=action,
        metadata_=resolved_metadata,
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
    buyer_id: int | None = None,
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
    _log_rfo_action(session, rfo_id, action, metadata, buyer_id=buyer_id)
    session.commit()
    session.refresh(rfo)
    return rfo, None


def close_rfo(
    session: Session,
    rfo_id: int,
    reason: str | None = None,
    buyer_id: int | None = None,
) -> tuple[RFO | None, str | None]:
    rfo, error = _transition_rfo(
        session, rfo_id, {"OPEN"}, "CLOSED", "close", reason, buyer_id=buyer_id
    )
    if not error and rfo:
        _enqueue_rfo_event(session, "rfo.closed", rfo)
    return rfo, error


def award_rfo(
    session: Session,
    rfo_id: int,
    reason: str | None = None,
    offer_id: int | None = None,
    buyer_id: int | None = None,
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
    _log_rfo_action(session, rfo_id, "award", metadata, buyer_id=buyer_id)

    session.commit()
    session.refresh(rfo)
    _enqueue_rfo_event(session, "rfo.awarded", rfo, offer_id=offer_id)
    return rfo, None


def reopen_rfo(
    session: Session,
    rfo_id: int,
    reason: str | None = None,
    buyer_id: int | None = None,
) -> tuple[RFO | None, str | None]:
    return _transition_rfo(session, rfo_id, {"CLOSED"}, "OPEN", "reopen", reason, buyer_id=buyer_id)


def update_rfo_scoring_config(
    session: Session,
    rfo_id: int,
    scoring_version: str | None = None,
    weights: dict | None = None,
    buyer_id: int | None = None,
) -> RFO | None:
    rfo = session.get(RFO, rfo_id)
    if not rfo:
        return None
    if scoring_version:
        rfo.scoring_version = scoring_version
    if weights is not None:
        rfo.weights = weights
    session.add(rfo)
    _log_rfo_action(
        session,
        rfo_id,
        "scoring_update",
        {"scoring_version": rfo.scoring_version, "weights": rfo.weights},
        buyer_id=buyer_id,
    )
    session.commit()
    session.refresh(rfo)
    return rfo


def update_rfo(
    session: Session,
    rfo_id: int,
    buyer_id: int,
    updates: dict,
) -> tuple[RFO | None, str | None]:
    rfo = session.get(RFO, rfo_id)
    if not rfo:
        return None, "not_found"
    if rfo.buyer_id != buyer_id:
        return rfo, "forbidden"
    if rfo.status != "OPEN":
        return rfo, "invalid"

    if "category" in updates:
        rfo.category = updates["category"]
    if "title" in updates:
        rfo.title = updates["title"]
    if "summary" in updates:
        rfo.summary = updates["summary"]
    if "currency" in updates:
        rfo.currency = updates["currency"]
    if "quantity" in updates:
        rfo.quantity = updates["quantity"]
    if "quote_deadline_hours" in updates:
        rfo.quote_deadline_hours = updates["quote_deadline_hours"]
    if "location" in updates:
        rfo.location = updates["location"]
    if "expires_at" in updates:
        rfo.expires_at = updates["expires_at"]
    if "preferences" in updates:
        rfo.preferences = updates["preferences"]
    if "line_items" in updates:
        rfo.line_items = updates["line_items"]
    if "compliance" in updates:
        rfo.compliance = updates["compliance"]
    if "scoring_profile" in updates:
        rfo.scoring_profile = updates["scoring_profile"]

    base_constraints = updates.get("constraints", rfo.constraints)
    merged_constraints, resolved_budget_max, resolved_deadline, resolved_currency = _sync_request_fields(
        base_constraints,
        updates.get("budget_max", rfo.budget_max),
        updates.get("delivery_deadline_days", rfo.delivery_deadline_days),
        updates.get("currency", rfo.currency),
    )
    rfo.constraints = merged_constraints
    rfo.budget_max = resolved_budget_max
    rfo.delivery_deadline_days = resolved_deadline
    rfo.currency = resolved_currency

    session.add(rfo)
    _log_rfo_action(
        session,
        rfo_id,
        "update",
        {"fields": sorted(updates.keys())},
        buyer_id=buyer_id,
    )
    session.commit()
    session.refresh(rfo)
    return rfo, None
