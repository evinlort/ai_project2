from fastapi import APIRouter, Depends
from sqlmodel import Session

from intentbid.app.api.deps import require_vendor
from intentbid.app.core.schemas import (
    VendorMeResponse,
    VendorRegisterRequest,
    VendorRegisterResponse,
)
from intentbid.app.db.session import get_session
from intentbid.app.services.vendor_service import register_vendor

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
