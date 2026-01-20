from datetime import datetime, timezone
from typing import Any, Dict

from pydantic import BaseModel, Field, field_validator


class VendorRegisterRequest(BaseModel):
    name: str


class VendorRegisterResponse(BaseModel):
    vendor_id: int
    api_key: str


class VendorMeResponse(BaseModel):
    vendor_id: int
    name: str


class VendorProfileRequest(BaseModel):
    categories: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    lead_time_days: int | None = Field(default=None, gt=0)
    min_order_value: float | None = Field(default=None, gt=0)


class VendorProfileResponse(BaseModel):
    vendor_id: int
    categories: list[str]
    regions: list[str]
    lead_time_days: int | None
    min_order_value: float | None


class BuyerRegisterRequest(BaseModel):
    name: str


class BuyerRegisterResponse(BaseModel):
    buyer_id: int
    api_key: str


class BuyerMeResponse(BaseModel):
    buyer_id: int
    name: str


class VendorWebhookCreateRequest(BaseModel):
    url: str


class VendorWebhookCreateResponse(BaseModel):
    webhook_id: int
    url: str
    secret: str


class VendorOnboardingStatusResponse(BaseModel):
    vendor_id: int
    steps: Dict[str, bool]


class VendorKeyCreateResponse(BaseModel):
    key_id: int
    api_key: str
    status: str
    created_at: datetime


class VendorKeyRevokeResponse(BaseModel):
    key_id: int
    status: str
    revoked_at: datetime | None


class RFOCreate(BaseModel):
    category: str
    constraints: Dict[str, Any]
    preferences: Dict[str, Any]
    title: str | None = None
    summary: str | None = None
    budget_max: float | None = Field(default=None, gt=0)
    currency: str | None = None
    delivery_deadline_days: int | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, gt=0)
    location: str | None = None
    expires_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Title cannot be empty")
        return value

    @field_validator("expires_at")
    @classmethod
    def _expires_at_in_future(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        resolved = value
        if resolved.tzinfo is None:
            resolved = resolved.replace(tzinfo=timezone.utc)
        if resolved <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")
        return value


class RFOUpdateRequest(BaseModel):
    category: str | None = None
    constraints: Dict[str, Any] | None = None
    preferences: Dict[str, Any] | None = None
    title: str | None = None
    summary: str | None = None
    budget_max: float | None = Field(default=None, gt=0)
    currency: str | None = None
    delivery_deadline_days: int | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, gt=0)
    location: str | None = None
    expires_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Title cannot be empty")
        return value

    @field_validator("expires_at")
    @classmethod
    def _expires_at_in_future(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        resolved = value
        if resolved.tzinfo is None:
            resolved = resolved.replace(tzinfo=timezone.utc)
        if resolved <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")
        return value


class RFOCreateResponse(BaseModel):
    rfo_id: int
    status: str


class RFOStatusUpdateRequest(BaseModel):
    reason: str | None = None
    offer_id: int | None = None


class RFOStatusUpdateResponse(BaseModel):
    rfo_id: int
    status: str
    reason: str | None = None


class RFOScoringUpdateRequest(BaseModel):
    scoring_version: str | None = None
    weights: Dict[str, float] | None = None


class RFOScoringUpdateResponse(BaseModel):
    rfo_id: int
    scoring_version: str
    weights: Dict[str, float]


class RFODetailResponse(BaseModel):
    id: int
    category: str
    title: str | None = None
    summary: str | None = None
    budget_max: float | None = None
    currency: str | None = None
    delivery_deadline_days: int | None = None
    quantity: int | None = None
    location: str | None = None
    expires_at: datetime | None = None
    constraints: Dict[str, Any]
    preferences: Dict[str, Any]
    status: str
    created_at: datetime
    offers_count: int


class RFOListItem(BaseModel):
    id: int
    category: str
    title: str | None = None
    summary: str | None = None
    budget_max: float | None = None
    currency: str | None = None
    delivery_deadline_days: int | None = None
    quantity: int | None = None
    location: str | None = None
    expires_at: datetime | None = None
    status: str
    created_at: datetime


class RFOListResponse(BaseModel):
    items: list[RFOListItem]
    total: int
    limit: int
    offset: int


class RFORequestSummary(BaseModel):
    id: int
    title: str | None = None
    category: str
    status: str


class VendorOfferListItem(BaseModel):
    offer_id: int
    rfo_id: int
    price_amount: float
    currency: str
    delivery_eta_days: int
    warranty_months: int
    return_days: int
    stock: bool
    metadata: Dict[str, Any]
    created_at: datetime
    status: str
    is_awarded: bool
    request: RFORequestSummary


class VendorOfferListResponse(BaseModel):
    items: list[VendorOfferListItem]
    total: int
    limit: int
    offset: int


class VendorMatchItem(BaseModel):
    rfo: RFOListItem
    reasons: list[str]


class VendorMatchesResponse(BaseModel):
    items: list[VendorMatchItem]
    total: int
    limit: int
    offset: int


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


class OfferPublic(BaseModel):
    id: int
    rfo_id: int
    vendor_id: int
    price_amount: float
    currency: str
    delivery_eta_days: int
    warranty_months: int
    return_days: int
    stock: bool
    metadata: Dict[str, Any]
    created_at: datetime


class RFOOffersResponse(BaseModel):
    rfo_id: int
    offers: list[OfferPublic]


class BestOffer(BaseModel):
    offer_id: int
    vendor_id: int
    score: float
    explain: Dict[str, Any]
    offer: OfferPublic


class BestOffersResponse(BaseModel):
    rfo_id: int
    top_offers: list[BestOffer]


class BuyerRankingResponse(BaseModel):
    rfo_id: int
    offers: list[BestOffer]


class RFOExplainResponse(BaseModel):
    rfo_id: int
    scoring_version: str
    offers: list[BestOffer]
