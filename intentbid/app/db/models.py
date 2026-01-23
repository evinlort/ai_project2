from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.types import DateTime, TypeDecorator
from sqlmodel import Field, Relationship, SQLModel


class Vendor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    api_key_hash: str
    verification_status: str = Field(default="UNVERIFIED", index=True)
    verification_notes: Optional[str] = Field(default=None)
    verified_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    offers: List["Offer"] = Relationship(back_populates="vendor")
    api_keys: List["VendorApiKey"] = Relationship(back_populates="vendor")
    profile: Optional["VendorProfile"] = Relationship(back_populates="vendor")


class VendorApiKey(SQLModel, table=True):
    __tablename__ = "vendor_api_key"

    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id", index=True)
    hashed_key: str = Field(sa_column=Column(String, unique=True, index=True))
    status: str = Field(default="active", index=True)
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: Optional[datetime] = None

    vendor: Optional[Vendor] = Relationship(back_populates="api_keys")


class VendorWebhook(SQLModel, table=True):
    __tablename__ = "vendor_webhook"

    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id", index=True)
    url: str
    secret: str
    is_active: bool = Field(default=True, index=True)
    last_delivery_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VendorProfile(SQLModel, table=True):
    __tablename__ = "vendor_profile"

    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id", index=True)
    categories: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    regions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    lead_time_days: Optional[int] = Field(default=None, index=True)
    min_order_value: Optional[float] = Field(default=None, index=True)
    on_time_delivery_rate: Optional[float] = Field(default=None)
    dispute_rate: Optional[float] = Field(default=None)
    verified_distributor: bool = Field(default=False)

    vendor: Optional[Vendor] = Relationship(back_populates="profile")


class Part(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("manufacturer", "mpn", name="uq_part_manufacturer_mpn"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    manufacturer: str = Field(index=True)
    mpn: str = Field(index=True)
    category: str = Field(index=True)
    key_specs: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    aliases: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class EventOutbox(SQLModel, table=True):
    __tablename__ = "event_outbox"

    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id", index=True)
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = Field(default="pending", index=True)
    attempts: int = Field(default=0)
    last_error: Optional[str] = None
    next_attempt_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IdempotencyKey(SQLModel, table=True):
    __tablename__ = "idempotency_key"
    __table_args__ = (
        UniqueConstraint("key", "endpoint", name="uq_idempotency_key_endpoint"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True)
    endpoint: str = Field(index=True)
    status_code: int
    response_body: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PlanLimit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_code: str = Field(index=True)
    max_offers_per_month: int
    max_rfos_per_month: Optional[int] = Field(default=None)
    max_awards_per_month: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id", index=True)
    plan_code: str
    status: str = Field(default="active", index=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None


class UsageEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id", index=True)
    event_type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BuyerSubscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    buyer_id: int = Field(foreign_key="buyer.id", index=True)
    plan_code: str
    status: str = Field(default="active", index=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None


class BuyerUsageEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    buyer_id: int = Field(foreign_key="buyer.id", index=True)
    event_type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Buyer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    api_keys: List["BuyerApiKey"] = Relationship(back_populates="buyer")
    rfos: List["RFO"] = Relationship(back_populates="buyer")


class BuyerApiKey(SQLModel, table=True):
    __tablename__ = "buyer_api_key"

    id: Optional[int] = Field(default=None, primary_key=True)
    buyer_id: int = Field(foreign_key="buyer.id", index=True)
    hashed_key: str = Field(sa_column=Column(String, unique=True, index=True))
    status: str = Field(default="active", index=True)
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: Optional[datetime] = None

    buyer: Optional[Buyer] = Relationship(back_populates="api_keys")


class RFO(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    buyer_id: Optional[int] = Field(default=None, foreign_key="buyer.id", index=True)
    category: str
    title: Optional[str] = Field(default=None, index=True)
    summary: Optional[str] = Field(default=None)
    budget_max: Optional[float] = Field(default=None, index=True)
    currency: Optional[str] = Field(default=None, index=True)
    delivery_deadline_days: Optional[int] = Field(default=None, index=True)
    quote_deadline_hours: Optional[int] = Field(default=None, index=True)
    quantity: Optional[int] = Field(default=None, index=True)
    location: Optional[str] = Field(default=None, index=True)
    expires_at: Optional[datetime] = Field(
        default=None, sa_column=Column(UTCDateTime(), index=True)
    )
    constraints: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    preferences: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    line_items: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    compliance: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    scoring_profile: Optional[str] = Field(default=None)
    status: str = Field(default="OPEN", index=True)
    status_reason: Optional[str] = None
    awarded_offer_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("offer.id", use_alter=True, name="fk_rfo_awarded_offer_id"),
            index=True,
        ),
    )
    scoring_version: str = Field(default="v1")
    weights: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    offers: List["Offer"] = Relationship(
        back_populates="rfo",
        sa_relationship_kwargs={"foreign_keys": "Offer.rfo_id"},
    )
    buyer: Optional[Buyer] = Relationship(back_populates="rfos")


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(index=True)
    entity_id: int = Field(index=True)
    action: str
    metadata_: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON),
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Offer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rfo_id: int = Field(foreign_key="rfo.id")
    vendor_id: int = Field(foreign_key="vendor.id")
    price_amount: float
    currency: str
    delivery_eta_days: int
    warranty_months: int
    return_days: int
    stock: bool
    offer_version: int = Field(default=1, index=True)
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(UTCDateTime()))
    unit_price: Optional[float] = Field(default=None)
    available_qty: Optional[int] = Field(default=None)
    lead_time_days: Optional[int] = Field(default=None)
    shipping_cost: Optional[float] = Field(default=None)
    tax_estimate: Optional[float] = Field(default=None)
    condition: Optional[str] = Field(default=None)
    traceability: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    valid_until: Optional[datetime] = Field(default=None, sa_column=Column(UTCDateTime()))
    status: str = Field(default="submitted", index=True)
    is_awarded: bool = Field(default=False, index=True)
    metadata_: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON),
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    vendor: Optional[Vendor] = Relationship(back_populates="offers")
    rfo: Optional[RFO] = Relationship(
        back_populates="offers",
        sa_relationship_kwargs={"foreign_keys": "Offer.rfo_id"},
    )


class OfferRevision(SQLModel, table=True):
    __tablename__ = "offer_revision"

    id: Optional[int] = Field(default=None, primary_key=True)
    offer_id: int = Field(foreign_key="offer.id", index=True)
    offer_version: int
    snapshot: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
