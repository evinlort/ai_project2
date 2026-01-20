import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlmodel import Session, SQLModel

from intentbid.app.core.schemas import OfferCreate
from intentbid.app.db.models import RFO, VendorProfile
from intentbid.app.db.session import engine
from intentbid.app.services.buyer_service import register_buyer
from intentbid.app.services.offer_service import create_offer
from intentbid.app.services.vendor_service import register_vendor

random.seed(42)

CATEGORIES = ["sneakers", "laptop", "chair", "headphones", "backpack"]
VENDOR_NAMES = ["Aurora Supply", "Northwind", "Lumen Goods", "Cobalt", "Juniper"]
BUYER_NAMES = ["Atlas Procurement", "Brightline Retail", "Urban Outfit", "Nimbus Labs"]
REGIONS = ["NA", "EU", "APAC"]
LOCATIONS = ["Berlin", "Austin", "Toronto", "Seoul", "London"]
PREFERENCE_PRESETS = [
    {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1},
    {"w_price": 0.5, "w_delivery": 0.2, "w_warranty": 0.3},
    {"w_price": 0.7, "w_delivery": 0.2, "w_warranty": 0.1},
]


SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    vendors = []
    for name in VENDOR_NAMES:
        vendor, api_key = register_vendor(session, name)
        vendors.append({"id": vendor.id, "name": name, "api_key": api_key})

    buyers = []
    for name in BUYER_NAMES:
        buyer, api_key = register_buyer(session, name)
        buyers.append({"id": buyer.id, "name": name, "api_key": api_key})

    for vendor in vendors:
        profile = VendorProfile(
            vendor_id=vendor["id"],
            categories=random.sample(CATEGORIES, k=random.randint(1, 3)),
            regions=random.sample(REGIONS, k=random.randint(1, 2)),
            lead_time_days=random.randint(2, 10),
            min_order_value=random.choice([250, 500, 1000, 1500]),
        )
        session.add(profile)

    rfos = []
    for _ in range(random.randint(5, 10)):
        budget = random.randint(80, 300)
        category = random.choice(CATEGORIES)
        delivery_deadline = random.randint(2, 7)
        location = random.choice(LOCATIONS)
        buyer = random.choice(buyers)
        rfo = RFO(
            category=category,
            title=f"{category.title()} bulk request",
            summary=f"Ship to {location} with clear delivery expectations.",
            budget_max=budget,
            currency="USD",
            delivery_deadline_days=delivery_deadline,
            quantity=random.randint(25, 250),
            location=location,
            expires_at=datetime.now(timezone.utc) + timedelta(days=random.randint(7, 30)),
            constraints={
                "budget_max": budget,
                "size": random.choice(["S", "M", "L", 42]),
                "delivery_deadline_days": delivery_deadline,
            },
            preferences=random.choice(PREFERENCE_PRESETS),
            buyer_id=buyer["id"],
        )
        session.add(rfo)
        rfos.append(rfo)

    session.commit()
    for rfo in rfos:
        session.refresh(rfo)

    for _ in range(random.randint(20, 40)):
        vendor = random.choice(vendors)
        rfo = random.choice(rfos)
        budget = rfo.constraints.get("budget_max", 150)
        price = round(budget * random.uniform(0.7, 1.2), 2)
        eta = random.randint(1, 6)
        warranty = random.choice([6, 12, 18, 24])

        payload = OfferCreate(
            rfo_id=rfo.id,
            price_amount=price,
            currency="USD",
            delivery_eta_days=eta,
            warranty_months=warranty,
            return_days=random.choice([14, 30, 45]),
            stock=random.choice([True, True, True, False]),
            metadata={"sku": f"SKU-{random.randint(100, 999)}"},
        )
        create_offer(session, vendor["id"], payload)

    output_path = Path(__file__).with_name("demo_vendors.json")
    output_path.write_text(json.dumps(vendors, indent=2))
    buyer_output_path = Path(__file__).with_name("demo_buyers.json")
    buyer_output_path.write_text(json.dumps(buyers, indent=2))

    print("Seeded vendors:")
    for vendor in vendors:
        print(f"- {vendor['name']} (id={vendor['id']}) api_key={vendor['api_key']}")
    print(f"Saved vendor keys to {output_path}")
    print("Seeded buyers:")
    for buyer in buyers:
        print(f"- {buyer['name']} (id={buyer['id']}) api_key={buyer['api_key']}")
    print(f"Saved buyer keys to {buyer_output_path}")
