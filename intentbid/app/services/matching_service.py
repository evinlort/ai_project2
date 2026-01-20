from sqlmodel import Session, select

from intentbid.app.db.models import RFO, VendorProfile


def list_vendor_matches(
    session: Session,
    vendor_id: int,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[tuple[RFO, list[str]]], int]:
    profile = session.exec(
        select(VendorProfile).where(VendorProfile.vendor_id == vendor_id)
    ).first()
    if not profile:
        return [], 0

    rfos = session.exec(
        select(RFO).where(RFO.status == "OPEN").order_by(RFO.created_at.desc())
    ).all()

    matches: list[tuple[RFO, list[str]]] = []
    for rfo in rfos:
        reasons: list[str] = []
        if profile.categories:
            if rfo.category in profile.categories:
                reasons.append("category_match")
            else:
                continue
        if profile.regions:
            if rfo.location in profile.regions:
                reasons.append("region_match")
            else:
                continue
        matches.append((rfo, reasons))

    total = len(matches)
    return matches[offset : offset + limit], total
