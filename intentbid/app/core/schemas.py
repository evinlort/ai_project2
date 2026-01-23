from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_serializer, field_validator, model_validator


class PartCategory(str, Enum):
    GPU = "GPU"
    MEMORY = "MEMORY"
    SSD = "SSD"
    NIC = "NIC"


class GpuSpecs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chip: str
    vram_gb: int = Field(gt=0)
    form_factor: str
    condition: str
    interface: str


class MemorySpecs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    capacity_gb: int = Field(gt=0)
    speed_mt_s: int = Field(gt=0)
    ecc: bool
    form_factor: str


class SsdSpecs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interface: str
    capacity_tb: float = Field(gt=0)
    endurance_dwpd: float = Field(gt=0)
    form_factor: str


class NicSpecs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    speed_gbps: int = Field(gt=0)
    ports: int = Field(gt=0)
    interface: str
    rdma: bool


_PART_SPECS_BY_CATEGORY = {
    PartCategory.GPU: GpuSpecs,
    PartCategory.MEMORY: MemorySpecs,
    PartCategory.SSD: SsdSpecs,
    PartCategory.NIC: NicSpecs,
}


class PartCreate(BaseModel):
    manufacturer: str
    mpn: str
    category: PartCategory
    key_specs: Dict[str, Any]
    aliases: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_key_specs(self):
        spec_model = _PART_SPECS_BY_CATEGORY.get(self.category)
        if spec_model is None:
            raise ValueError(f"Unsupported category: {self.category}")
        try:
            spec = spec_model(**self.key_specs)
        except ValidationError as exc:
            raise ValueError("Invalid key_specs for category") from exc
        self.key_specs = spec.model_dump()
        return self


class PartPublic(BaseModel):
    id: int
    manufacturer: str
    mpn: str
    category: PartCategory
    key_specs: Dict[str, Any]
    aliases: List[str]
    created_at: datetime


class RFQLineItem(BaseModel):
    part_id: int | None = None
    mpn: str | None = None
    quantity: int = Field(gt=0)
    required_specs: Dict[str, Any] | None = None
    acceptable_alternates: List[str] | None = None

    @model_validator(mode="after")
    def _require_part_identifier(self):
        if not self.part_id and not self.mpn:
            raise ValueError("line_items require part_id or mpn")
        return self


class RFQCompliance(BaseModel):
    model_config = ConfigDict(extra="allow")

    export_control_ack: bool | None = None
    country_restrictions: List[str] | None = None


class OfferTraceability(BaseModel):
    model_config = ConfigDict(extra="allow")

    authorized_channel: bool | None = None
    invoices_available: bool | None = None
    serials_available: bool | None = None
    notes: str | None = None


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
    on_time_delivery_rate: float | None = None
    dispute_rate: float | None = None
    verified_distributor: bool | None = None


class VendorVerificationRequest(BaseModel):
    notes: str | None = None


class VendorVerificationResponse(BaseModel):
    vendor_id: int
    verification_status: str
    verification_notes: str | None = None
    verified_at: datetime | None = None


class VendorReputationUpdateRequest(BaseModel):
    on_time_delivery_rate: float | None = Field(default=None, ge=0, le=1)
    dispute_rate: float | None = Field(default=None, ge=0, le=1)
    verified_distributor: bool | None = None


class VendorReputationResponse(BaseModel):
    vendor_id: int
    on_time_delivery_rate: float | None = None
    dispute_rate: float | None = None
    verified_distributor: bool | None = None


class AdminSubscriptionRequest(BaseModel):
    plan_code: str
    status: str = "active"


class AdminSubscriptionResponse(BaseModel):
    subscription_id: int
    plan_code: str
    status: str


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
    constraints: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    compliance: Dict[str, Any] = Field(default_factory=dict)
    scoring_profile: str | None = None
    title: str | None = None
    summary: str | None = None
    budget_max: float | None = Field(default=None, gt=0)
    currency: str | None = None
    delivery_deadline_days: int | None = Field(default=None, gt=0)
    quote_deadline_hours: int | None = Field(default=None, gt=0)
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
        comparison_now = datetime.now(timezone.utc) - timedelta(seconds=5)
        if resolved <= comparison_now:
            raise ValueError("expires_at must be in the future")
        return value

    @field_validator("category")
    @classmethod
    def _normalize_category(cls, value: str) -> str:
        trimmed = value.strip()
        resolved = trimmed.upper()
        if resolved in {category.value for category in PartCategory}:
            return resolved
        return trimmed

    @field_validator("line_items")
    @classmethod
    def _validate_line_items(cls, value: List[Dict[str, Any]]):
        validated = []
        for item in value or []:
            validated_item = RFQLineItem(**item)
            validated.append(validated_item.model_dump(exclude_none=True))
        return validated

    @field_validator("compliance")
    @classmethod
    def _validate_compliance(cls, value: Dict[str, Any]):
        if not value:
            return {}
        return RFQCompliance(**value).model_dump(exclude_unset=True)


class RFOUpdateRequest(BaseModel):
    category: str | None = None
    constraints: Dict[str, Any] | None = None
    preferences: Dict[str, Any] | None = None
    line_items: List[Dict[str, Any]] | None = None
    compliance: Dict[str, Any] | None = None
    scoring_profile: str | None = None
    title: str | None = None
    summary: str | None = None
    budget_max: float | None = Field(default=None, gt=0)
    currency: str | None = None
    delivery_deadline_days: int | None = Field(default=None, gt=0)
    quote_deadline_hours: int | None = Field(default=None, gt=0)
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
        comparison_now = datetime.now(timezone.utc) - timedelta(seconds=5)
        if resolved <= comparison_now:
            raise ValueError("expires_at must be in the future")
        return value

    @field_validator("category")
    @classmethod
    def _normalize_category(cls, value: str | None) -> str | None:
        if value is None:
            return value
        trimmed = value.strip()
        resolved = trimmed.upper()
        if resolved in {category.value for category in PartCategory}:
            return resolved
        return trimmed

    @field_validator("line_items")
    @classmethod
    def _validate_line_items(cls, value: List[Dict[str, Any]] | None):
        if value is None:
            return value
        validated = []
        for item in value:
            validated_item = RFQLineItem(**item)
            validated.append(validated_item.model_dump(exclude_none=True))
        return validated

    @field_validator("compliance")
    @classmethod
    def _validate_compliance(cls, value: Dict[str, Any] | None):
        if value is None:
            return value
        if not value:
            return {}
        return RFQCompliance(**value).model_dump(exclude_unset=True)


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
    quote_deadline_hours: int | None = None
    quantity: int | None = None
    location: str | None = None
    expires_at: datetime | None = None
    constraints: Dict[str, Any]
    preferences: Dict[str, Any]
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    compliance: Dict[str, Any] = Field(default_factory=dict)
    scoring_profile: str | None = None
    status: str
    created_at: datetime
    offers_count: int

    @field_serializer("expires_at")
    def _serialize_expires_at(self, value: datetime | None, _info):
        if value is None:
            return None
        return value.isoformat()


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

    @field_serializer("expires_at")
    def _serialize_expires_at(self, value: datetime | None, _info):
        if value is None:
            return None
        return value.isoformat()


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
    price_amount: float | None = None
    unit_price: float | None = None
    currency: str
    delivery_eta_days: int | None = None
    lead_time_days: int | None = None
    available_qty: int | None = None
    shipping_cost: float | None = None
    tax_estimate: float | None = None
    condition: str | None = None
    warranty_months: int | None = None
    return_days: int | None = None
    stock: bool | None = None
    traceability: Dict[str, Any] = Field(default_factory=dict)
    valid_until: datetime | None = None
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
    price_amount: float | None = None
    unit_price: float | None = None
    currency: str
    delivery_eta_days: int | None = None
    lead_time_days: int | None = None
    available_qty: int | None = None
    shipping_cost: float | None = None
    tax_estimate: float | None = None
    condition: str | None = None
    warranty_months: int
    return_days: int
    stock: bool | None = None
    traceability: Dict[str, Any] = Field(default_factory=dict)
    valid_until: datetime | None = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_price_and_lead_time(self):
        if self.price_amount is None and self.unit_price is None:
            raise ValueError("price_amount or unit_price is required")
        if self.delivery_eta_days is None and self.lead_time_days is None:
            raise ValueError("delivery_eta_days or lead_time_days is required")
        return self

    @field_validator("traceability")
    @classmethod
    def _validate_traceability(cls, value: Dict[str, Any]):
        if not value:
            return {}
        return OfferTraceability(**value).model_dump(exclude_unset=True)

    @field_validator("valid_until")
    @classmethod
    def _valid_until_in_future(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        resolved = value
        if resolved.tzinfo is None:
            resolved = resolved.replace(tzinfo=timezone.utc)
        if resolved <= datetime.now(timezone.utc) - timedelta(seconds=5):
            raise ValueError("valid_until must be in the future")
        return value


class OfferCreateResponse(BaseModel):
    offer_id: int


class OfferUpdateRequest(BaseModel):
    price_amount: float | None = None
    unit_price: float | None = None
    delivery_eta_days: int | None = None
    lead_time_days: int | None = None
    available_qty: int | None = None
    shipping_cost: float | None = None
    tax_estimate: float | None = None
    condition: str | None = None
    warranty_months: int | None = None
    return_days: int | None = None
    stock: bool | None = None
    traceability: Dict[str, Any] | None = None
    valid_until: datetime | None = None
    metadata: Dict[str, Any] | None = None

    @model_validator(mode="after")
    def _require_update_fields(self):
        if not any(
            value is not None
            for value in (
                self.price_amount,
                self.unit_price,
                self.delivery_eta_days,
                self.lead_time_days,
                self.available_qty,
                self.shipping_cost,
                self.tax_estimate,
                self.condition,
                self.warranty_months,
                self.return_days,
                self.stock,
                self.traceability,
                self.valid_until,
                self.metadata,
            )
        ):
            raise ValueError("At least one field must be provided")
        return self

    @field_validator("traceability")
    @classmethod
    def _validate_traceability(cls, value: Dict[str, Any] | None):
        if value is None:
            return value
        if not value:
            return {}
        return OfferTraceability(**value).model_dump(exclude_unset=True)

    @field_validator("valid_until")
    @classmethod
    def _valid_until_in_future(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        resolved = value
        if resolved.tzinfo is None:
            resolved = resolved.replace(tzinfo=timezone.utc)
        if resolved <= datetime.now(timezone.utc) - timedelta(seconds=5):
            raise ValueError("valid_until must be in the future")
        return value


class OfferUpdateResponse(BaseModel):
    offer_id: int
    offer_version: int


class OfferPublic(BaseModel):
    id: int
    rfo_id: int
    vendor_id: int
    price_amount: float | None = None
    unit_price: float | None = None
    currency: str
    delivery_eta_days: int | None = None
    lead_time_days: int | None = None
    available_qty: int | None = None
    shipping_cost: float | None = None
    tax_estimate: float | None = None
    condition: str | None = None
    warranty_months: int | None = None
    return_days: int | None = None
    stock: bool | None = None
    traceability: Dict[str, Any] = Field(default_factory=dict)
    valid_until: datetime | None = None
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


class RFORecommendationResponse(BaseModel):
    rfo_id: int
    offer_id: int
    score: float
    explain: Dict[str, Any]
    offer: OfferPublic
    rationale: str


class AutoAwardRequest(BaseModel):
    opt_in: bool = False
    reason: str | None = None
    min_score: float | None = Field(default=None, ge=0)


class AutoAwardResponse(BaseModel):
    rfo_id: int
    status: str
    offer_id: int
    score: float
    reason: str | None = None
