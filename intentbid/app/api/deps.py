from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from intentbid.app.db.models import Vendor
from intentbid.app.db.session import get_session
from intentbid.app.services.vendor_service import get_vendor_by_api_key


def require_vendor(
    api_key: str | None = Header(default=None, alias="X-API-Key"),
    session: Session = Depends(get_session),
) -> Vendor:
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    vendor = get_vendor_by_api_key(session, api_key)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return vendor
