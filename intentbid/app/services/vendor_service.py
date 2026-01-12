from sqlmodel import Session, select

from intentbid.app.core.security import generate_api_key, hash_api_key
from intentbid.app.db.models import Vendor


def register_vendor(session: Session, name: str) -> tuple[Vendor, str]:
    api_key = generate_api_key()
    vendor = Vendor(name=name, api_key_hash=hash_api_key(api_key))
    session.add(vendor)
    session.commit()
    session.refresh(vendor)
    return vendor, api_key


def get_vendor_by_api_key(session: Session, api_key: str) -> Vendor | None:
    api_key_hash = hash_api_key(api_key)
    return session.exec(
        select(Vendor).where(Vendor.api_key_hash == api_key_hash)
    ).first()
