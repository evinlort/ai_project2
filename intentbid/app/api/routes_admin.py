from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import Session

from intentbid.app.core.config import settings
from intentbid.app.core.schemas import (
    AdminSubscriptionRequest,
    AdminSubscriptionResponse,
    VendorReputationResponse,
    VendorReputationUpdateRequest,
    VendorVerificationRequest,
    VendorVerificationResponse,
)
from intentbid.app.db.models import Buyer, BuyerSubscription, Subscription, Vendor
from intentbid.app.db.session import get_session
from intentbid.app.services.admin_service import (
    set_vendor_verification_status,
    update_vendor_reputation,
)

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def require_admin_api_key(
    admin_key: str | None = Header(default=None, alias="X-Admin-API-Key"),
) -> None:
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API key not configured",
        )
    if not admin_key or admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key",
        )


@router.post(
    "/vendors/{vendor_id}/approve",
    response_model=VendorVerificationResponse,
    dependencies=[Depends(require_admin_api_key)],
)
def approve_vendor(
    vendor_id: int,
    payload: VendorVerificationRequest | None = None,
    session: Session = Depends(get_session),
) -> VendorVerificationResponse:
    vendor = set_vendor_verification_status(
        session,
        vendor_id=vendor_id,
        status="VERIFIED",
        notes=payload.notes if payload else None,
    )
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorVerificationResponse(
        vendor_id=vendor.id,
        verification_status=vendor.verification_status,
        verification_notes=vendor.verification_notes,
        verified_at=vendor.verified_at,
    )


@router.post(
    "/vendors/{vendor_id}/suspend",
    response_model=VendorVerificationResponse,
    dependencies=[Depends(require_admin_api_key)],
)
def suspend_vendor(
    vendor_id: int,
    payload: VendorVerificationRequest | None = None,
    session: Session = Depends(get_session),
) -> VendorVerificationResponse:
    vendor = set_vendor_verification_status(
        session,
        vendor_id=vendor_id,
        status="SUSPENDED",
        notes=payload.notes if payload else None,
    )
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorVerificationResponse(
        vendor_id=vendor.id,
        verification_status=vendor.verification_status,
        verification_notes=vendor.verification_notes,
        verified_at=vendor.verified_at,
    )


@router.patch(
    "/vendors/{vendor_id}/reputation",
    response_model=VendorReputationResponse,
    dependencies=[Depends(require_admin_api_key)],
)
def update_reputation(
    vendor_id: int,
    payload: VendorReputationUpdateRequest,
    session: Session = Depends(get_session),
) -> VendorReputationResponse:
    profile = update_vendor_reputation(
        session,
        vendor_id=vendor_id,
        on_time_delivery_rate=payload.on_time_delivery_rate,
        dispute_rate=payload.dispute_rate,
        verified_distributor=payload.verified_distributor,
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorReputationResponse(
        vendor_id=vendor_id,
        on_time_delivery_rate=profile.on_time_delivery_rate,
        dispute_rate=profile.dispute_rate,
        verified_distributor=profile.verified_distributor,
    )


@router.post(
    "/buyers/{buyer_id}/subscription",
    response_model=AdminSubscriptionResponse,
    dependencies=[Depends(require_admin_api_key)],
)
def create_buyer_subscription(
    buyer_id: int,
    payload: AdminSubscriptionRequest,
    session: Session = Depends(get_session),
) -> AdminSubscriptionResponse:
    buyer = session.get(Buyer, buyer_id)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    subscription = BuyerSubscription(
        buyer_id=buyer_id,
        plan_code=payload.plan_code,
        status=payload.status,
    )
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return AdminSubscriptionResponse(
        subscription_id=subscription.id,
        plan_code=subscription.plan_code,
        status=subscription.status,
    )


@router.post(
    "/vendors/{vendor_id}/subscription",
    response_model=AdminSubscriptionResponse,
    dependencies=[Depends(require_admin_api_key)],
)
def create_vendor_subscription(
    vendor_id: int,
    payload: AdminSubscriptionRequest,
    session: Session = Depends(get_session),
) -> AdminSubscriptionResponse:
    vendor = session.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    subscription = Subscription(
        vendor_id=vendor_id,
        plan_code=payload.plan_code,
        status=payload.status,
    )
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return AdminSubscriptionResponse(
        subscription_id=subscription.id,
        plan_code=subscription.plan_code,
        status=subscription.status,
    )
