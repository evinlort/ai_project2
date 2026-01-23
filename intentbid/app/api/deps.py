from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from intentbid.app.core.config import settings
from intentbid.app.core.rate_limit import rate_limiter
from intentbid.app.db.models import Buyer, Vendor
from intentbid.app.db.session import get_session
from intentbid.app.services.buyer_service import get_buyer_by_api_key
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
    if not rate_limiter.allow(api_key, settings.rate_limit_requests, settings.rate_limit_window_seconds):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    return vendor


def require_buyer(
    api_key: str | None = Header(default=None, alias="X-Buyer-API-Key"),
    session: Session = Depends(get_session),
) -> Buyer:
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    buyer = get_buyer_by_api_key(session, api_key)
    if not buyer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if not rate_limiter.allow(api_key, settings.rate_limit_requests, settings.rate_limit_window_seconds):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    return buyer


def optional_buyer(
    api_key: str | None = Header(default=None, alias="X-Buyer-API-Key"),
    session: Session = Depends(get_session),
) -> Buyer | None:
    if not api_key:
        return None

    buyer = get_buyer_by_api_key(session, api_key)
    if not buyer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if not rate_limiter.allow(api_key, settings.rate_limit_requests, settings.rate_limit_window_seconds):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    return buyer
