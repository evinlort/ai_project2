from sqlalchemy import func
from sqlmodel import Session, select

from intentbid.app.db.models import Offer, RFO


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
