from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, JSON, String
from sqlmodel import Field, Relationship, SQLModel


class Vendor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    api_key_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    offers: List["Offer"] = Relationship(back_populates="vendor")
    api_keys: List["VendorApiKey"] = Relationship(back_populates="vendor")


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


class Buyer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    api_keys: List["BuyerApiKey"] = Relationship(back_populates="buyer")


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
    category: str
    constraints: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    preferences: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = Field(default="OPEN", index=True)
    status_reason: Optional[str] = None
    scoring_version: str = Field(default="v1")
    weights: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    offers: List["Offer"] = Relationship(back_populates="rfo")


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
    metadata_: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON),
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    vendor: Optional[Vendor] = Relationship(back_populates="offers")
    rfo: Optional[RFO] = Relationship(back_populates="offers")
