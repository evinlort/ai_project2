import json
import random
from pathlib import Path

from sqlmodel import Session, SQLModel

from intentbid.app.core.schemas import OfferCreate
from intentbid.app.db.models import RFO
from intentbid.app.db.session import engine
from intentbid.app.services.offer_service import create_offer
from intentbid.app.services.vendor_service import register_vendor

random.seed(42)

CATEGORIES = ["sneakers", "laptop", "chair", "headphones", "backpack"]
VENDOR_NAMES = ["Aurora Supply", "Northwind", "Lumen Goods", "Cobalt", "Juniper"]
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

    rfos = []
    for _ in range(random.randint(5, 10)):
        budget = random.randint(80, 300)
        rfo = RFO(
            category=random.choice(CATEGORIES),
            constraints={
                "budget_max": budget,
                "size": random.choice(["S", "M", "L", 42]),
                "delivery_deadline_days": random.randint(2, 7),
            },
            preferences=random.choice(PREFERENCE_PRESETS),
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

    print("Seeded vendors:")
    for vendor in vendors:
        print(f"- {vendor['name']} (id={vendor['id']}) api_key={vendor['api_key']}")
    print(f"Saved vendor keys to {output_path}")
