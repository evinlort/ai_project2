from sqlmodel import Session

from intentbid.app.core.schemas import OfferCreate
from intentbid.app.db.models import Offer


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
    return offer
