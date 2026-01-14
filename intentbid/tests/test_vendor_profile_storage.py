from sqlmodel import select

from intentbid.app.db.models import Vendor, VendorProfile


def test_vendor_profile_can_be_created_and_fetched(session):
    vendor = Vendor(name="Acme", api_key_hash="hash")
    session.add(vendor)
    session.commit()
    session.refresh(vendor)

    profile = VendorProfile(
        vendor_id=vendor.id,
        categories=["sneakers", "bags"],
        regions=["EU", "US"],
        lead_time_days=5,
        min_order_value=250.0,
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)

    fetched = session.exec(
        select(VendorProfile).where(VendorProfile.vendor_id == vendor.id)
    ).first()

    assert fetched is not None
    assert fetched.categories == ["sneakers", "bags"]
    assert fetched.regions == ["EU", "US"]
    assert fetched.lead_time_days == 5
    assert fetched.min_order_value == 250.0
