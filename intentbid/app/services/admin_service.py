from datetime import datetime, timezone

from sqlmodel import Session

from intentbid.app.db.models import Vendor, VendorProfile
from intentbid.app.services.vendor_service import get_vendor_profile


def set_vendor_verification_status(
    session: Session,
    vendor_id: int,
    status: str,
    notes: str | None = None,
) -> Vendor | None:
    vendor = session.get(Vendor, vendor_id)
    if not vendor:
        return None
    vendor.verification_status = status
    vendor.verification_notes = notes
    if status == "VERIFIED":
        vendor.verified_at = datetime.now(timezone.utc)
    elif status == "UNVERIFIED":
        vendor.verified_at = None
    session.add(vendor)
    session.commit()
    session.refresh(vendor)
    return vendor


def update_vendor_reputation(
    session: Session,
    vendor_id: int,
    on_time_delivery_rate: float | None = None,
    dispute_rate: float | None = None,
    verified_distributor: bool | None = None,
) -> VendorProfile | None:
    vendor = session.get(Vendor, vendor_id)
    if not vendor:
        return None

    profile = get_vendor_profile(session, vendor_id)
    if not profile:
        profile = VendorProfile(
            vendor_id=vendor_id,
            categories=[],
            regions=[],
            lead_time_days=None,
            min_order_value=None,
        )

    if on_time_delivery_rate is not None:
        profile.on_time_delivery_rate = on_time_delivery_rate
    if dispute_rate is not None:
        profile.dispute_rate = dispute_rate
    if verified_distributor is not None:
        profile.verified_distributor = verified_distributor

    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
