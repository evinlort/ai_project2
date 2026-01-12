from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from intentbid.app.db.models import AuditLog, Offer, RFO


def create_rfo(session: Session, category: str, constraints: dict, preferences: dict) -> RFO:
    rfo = RFO(category=category, constraints=constraints, preferences=preferences)
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


def award_rfo(session: Session, rfo_id: int, reason: str | None = None) -> tuple[RFO | None, str | None]:
    return _transition_rfo(session, rfo_id, {"CLOSED"}, "AWARDED", "award", reason)


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
