from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel


class Vendor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    api_key_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    offers: List["Offer"] = Relationship(back_populates="vendor")


class RFO(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category: str
    constraints: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    preferences: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = Field(default="OPEN", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    offers: List["Offer"] = Relationship(back_populates="rfo")


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
    created_at: datetime = Field(default_factory=datetime.utcnow)

    vendor: Optional[Vendor] = Relationship(back_populates="offers")
    rfo: Optional[RFO] = Relationship(back_populates="offers")
