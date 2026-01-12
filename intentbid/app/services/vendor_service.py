from sqlmodel import Session

from intentbid.app.core.security import generate_api_key, hash_api_key
from intentbid.app.db.models import Vendor


def register_vendor(session: Session, name: str) -> tuple[Vendor, str]:
    api_key = generate_api_key()
    vendor = Vendor(name=name, api_key_hash=hash_api_key(api_key))
    session.add(vendor)
    session.commit()
    session.refresh(vendor)
    return vendor, api_key
