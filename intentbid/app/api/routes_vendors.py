from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from intentbid.app.api.deps import require_vendor
from intentbid.app.core.schemas import (
    VendorKeyCreateResponse,
    VendorKeyRevokeResponse,
    VendorMeResponse,
    VendorRegisterRequest,
    VendorRegisterResponse,
)
from intentbid.app.db.session import get_session
from intentbid.app.services.vendor_service import (
    create_vendor_key,
    register_vendor,
    revoke_vendor_key,
)

router = APIRouter(prefix="/v1/vendors", tags=["vendors"])


@router.post("/register", response_model=VendorRegisterResponse)
def register_vendor_route(
    payload: VendorRegisterRequest,
    session: Session = Depends(get_session),
) -> VendorRegisterResponse:
    vendor, api_key = register_vendor(session, payload.name)
    return VendorRegisterResponse(vendor_id=vendor.id, api_key=api_key)


@router.get("/me", response_model=VendorMeResponse)
def vendor_me(vendor=Depends(require_vendor)) -> VendorMeResponse:
    return VendorMeResponse(vendor_id=vendor.id, name=vendor.name)


@router.post("/keys", response_model=VendorKeyCreateResponse)
def create_vendor_key_route(
    vendor=Depends(require_vendor),
    session: Session = Depends(get_session),
) -> VendorKeyCreateResponse:
    key, api_key = create_vendor_key(session, vendor.id)
    return VendorKeyCreateResponse(
        key_id=key.id,
        api_key=api_key,
        status=key.status,
        created_at=key.created_at,
    )


@router.post("/keys/{key_id}/revoke", response_model=VendorKeyRevokeResponse)
def revoke_vendor_key_route(
    key_id: int,
    vendor=Depends(require_vendor),
    session: Session = Depends(get_session),
) -> VendorKeyRevokeResponse:
    key = revoke_vendor_key(session, vendor.id, key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
    return VendorKeyRevokeResponse(
        key_id=key.id,
        status=key.status,
        revoked_at=key.revoked_at,
    )
