from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class VendorRegisterRequest(BaseModel):
    name: str


class VendorRegisterResponse(BaseModel):
    vendor_id: int
    api_key: str


class VendorMeResponse(BaseModel):
    vendor_id: int
    name: str


class RFOCreate(BaseModel):
    category: str
    constraints: Dict[str, Any]
    preferences: Dict[str, Any]


class RFOCreateResponse(BaseModel):
    rfo_id: int
    status: str


class RFODetailResponse(BaseModel):
    id: int
    category: str
    constraints: Dict[str, Any]
    preferences: Dict[str, Any]
    status: str
    created_at: datetime
    offers_count: int


class OfferCreate(BaseModel):
    rfo_id: int
    price_amount: float
    currency: str
    delivery_eta_days: int
    warranty_months: int
    return_days: int
    stock: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OfferCreateResponse(BaseModel):
    offer_id: int
