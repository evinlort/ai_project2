from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from intentbid.app.core.schemas import RFOCreate, RFOCreateResponse, RFODetailResponse
from intentbid.app.db.session import get_session
from intentbid.app.services.rfo_service import create_rfo, get_rfo_with_offers_count

router = APIRouter(prefix="/v1/rfo", tags=["rfo"])


@router.post("", response_model=RFOCreateResponse)
def create_rfo_route(
    payload: RFOCreate,
    session: Session = Depends(get_session),
) -> RFOCreateResponse:
    rfo = create_rfo(session, payload.category, payload.constraints, payload.preferences)
    return RFOCreateResponse(rfo_id=rfo.id, status=rfo.status)


@router.get("/{rfo_id}", response_model=RFODetailResponse)
def get_rfo_route(
    rfo_id: int,
    session: Session = Depends(get_session),
) -> RFODetailResponse:
    rfo, offers_count = get_rfo_with_offers_count(session, rfo_id)
    if not rfo:
        raise HTTPException(status_code=404, detail="RFO not found")

    return RFODetailResponse(
        id=rfo.id,
        category=rfo.category,
        constraints=rfo.constraints,
        preferences=rfo.preferences,
        status=rfo.status,
        created_at=rfo.created_at,
        offers_count=offers_count,
    )
