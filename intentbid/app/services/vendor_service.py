from datetime import datetime

from sqlmodel import Session, select

from intentbid.app.core.security import generate_api_key, hash_api_key
from intentbid.app.db.models import Vendor, VendorApiKey


def register_vendor(session: Session, name: str) -> tuple[Vendor, str]:
    api_key = generate_api_key()
    hashed_key = hash_api_key(api_key)
    vendor = Vendor(name=name, api_key_hash=hashed_key)
    session.add(vendor)
    session.commit()
    session.refresh(vendor)
    key = VendorApiKey(vendor_id=vendor.id, hashed_key=hashed_key, status="active")
    session.add(key)
    session.commit()
    return vendor, api_key


def get_vendor_by_api_key(session: Session, api_key: str) -> Vendor | None:
    api_key_hash = hash_api_key(api_key)
    key = session.exec(
        select(VendorApiKey).where(
            VendorApiKey.hashed_key == api_key_hash,
        )
    ).first()
    if key:
        if key.status != "active":
            return None
        key.last_used_at = datetime.utcnow()
        session.add(key)
        session.commit()
        return session.get(Vendor, key.vendor_id)

    vendor = session.exec(
        select(Vendor).where(Vendor.api_key_hash == api_key_hash)
    ).first()
    if not vendor:
        return None

    key = VendorApiKey(
        vendor_id=vendor.id,
        hashed_key=api_key_hash,
        status="active",
        last_used_at=datetime.utcnow(),
    )
    session.add(key)
    session.commit()
    return vendor


def create_vendor_key(session: Session, vendor_id: int) -> tuple[VendorApiKey, str]:
    api_key = generate_api_key()
    key = VendorApiKey(
        vendor_id=vendor_id,
        hashed_key=hash_api_key(api_key),
        status="active",
    )
    session.add(key)
    session.commit()
    session.refresh(key)
    return key, api_key


def revoke_vendor_key(session: Session, vendor_id: int, key_id: int) -> VendorApiKey | None:
    key = session.get(VendorApiKey, key_id)
    if not key or key.vendor_id != vendor_id:
        return None
    if key.status != "revoked":
        key.status = "revoked"
        key.revoked_at = datetime.utcnow()
        session.add(key)
        session.commit()
        session.refresh(key)
    return key
