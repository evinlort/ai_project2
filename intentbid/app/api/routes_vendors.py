from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from intentbid.app.api.deps import require_vendor
from intentbid.app.core.schemas import (
    VendorKeyCreateResponse,
    VendorKeyRevokeResponse,
    VendorMeResponse,
    VendorRegisterRequest,
    VendorRegisterResponse,
    VendorOnboardingStatusResponse,
    VendorWebhookCreateRequest,
    VendorWebhookCreateResponse,
)
from intentbid.app.db.session import get_session
from intentbid.app.services.vendor_service import (
    create_vendor_key,
    register_vendor,
    revoke_vendor_key,
)
from intentbid.app.services.webhook_service import register_vendor_webhook
from intentbid.app.db.models import VendorApiKey, VendorWebhook

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


@router.post("/webhooks", response_model=VendorWebhookCreateResponse)
def create_vendor_webhook(
    payload: VendorWebhookCreateRequest,
    vendor=Depends(require_vendor),
    session: Session = Depends(get_session),
) -> VendorWebhookCreateResponse:
    webhook = register_vendor_webhook(session, vendor.id, payload.url)
    return VendorWebhookCreateResponse(
        webhook_id=webhook.id,
        url=webhook.url,
        secret=webhook.secret,
    )


@router.get("/onboarding/status", response_model=VendorOnboardingStatusResponse)
def get_onboarding_status(
    vendor=Depends(require_vendor),
    session: Session = Depends(get_session),
) -> VendorOnboardingStatusResponse:
    has_key = session.exec(
        select(VendorApiKey).where(
            VendorApiKey.vendor_id == vendor.id,
            VendorApiKey.status == "active",
        )
    ).first() is not None
    has_webhook = session.exec(
        select(VendorWebhook).where(
            VendorWebhook.vendor_id == vendor.id,
            VendorWebhook.is_active.is_(True),
        )
    ).first() is not None

    steps = {
        "api_key": has_key,
        "webhook": has_webhook,
        "test_call": False,
        "go_live": False,
    }
    return VendorOnboardingStatusResponse(vendor_id=vendor.id, steps=steps)
