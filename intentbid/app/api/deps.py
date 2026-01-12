from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session, select

from intentbid.app.core.security import hash_api_key
from intentbid.app.db.models import Vendor
from intentbid.app.db.session import get_session


def require_vendor(
    api_key: str | None = Header(default=None, alias="X-API-Key"),
    session: Session = Depends(get_session),
) -> Vendor:
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    api_key_hash = hash_api_key(api_key)
    vendor = session.exec(
        select(Vendor).where(Vendor.api_key_hash == api_key_hash)
    ).first()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return vendor
