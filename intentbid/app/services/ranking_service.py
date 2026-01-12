from sqlmodel import Session, select

from intentbid.app.core.scoring import score_offer
from intentbid.app.db.models import Offer, RFO


def get_best_offers(
    session: Session,
    rfo_id: int,
    top_k: int,
) -> tuple[RFO | None, list[tuple[Offer, float, dict]]]:
    rfo = session.get(RFO, rfo_id)
    if not rfo:
        return None, []

    offers = session.exec(select(Offer).where(Offer.rfo_id == rfo_id)).all()
    scored = [(offer, *score_offer(offer, rfo)) for offer in offers]
    scored.sort(key=lambda item: item[1], reverse=True)
    return rfo, scored[:top_k]


def get_ranked_offers(
    session: Session,
    rfo_id: int,
) -> tuple[RFO | None, list[tuple[Offer, float, dict]]]:
    rfo = session.get(RFO, rfo_id)
    if not rfo:
        return None, []

    offers = session.exec(select(Offer).where(Offer.rfo_id == rfo_id)).all()
    scored = [(offer, *score_offer(offer, rfo)) for offer in offers]
    scored.sort(key=lambda item: item[1], reverse=True)
    return rfo, scored
