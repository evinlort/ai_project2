from datetime import datetime, timezone

from sqlmodel import Session, select

from intentbid.app.core.security import generate_api_key, hash_api_key
from intentbid.app.db.models import Buyer, BuyerApiKey


def register_buyer(session: Session, name: str) -> tuple[Buyer, str]:
    api_key = generate_api_key()
    hashed_key = hash_api_key(api_key)
    buyer = Buyer(name=name)
    session.add(buyer)
    session.commit()
    session.refresh(buyer)

    key = BuyerApiKey(buyer_id=buyer.id, hashed_key=hashed_key, status="active")
    session.add(key)
    session.commit()
    return buyer, api_key


def get_buyer_by_api_key(session: Session, api_key: str) -> Buyer | None:
    api_key_hash = hash_api_key(api_key)
    key = session.exec(
        select(BuyerApiKey).where(BuyerApiKey.hashed_key == api_key_hash)
    ).first()
    if not key:
        return None
    if key.status != "active":
        return None

    key.last_used_at = datetime.now(timezone.utc)
    session.add(key)
    session.commit()
    return session.get(Buyer, key.buyer_id)
