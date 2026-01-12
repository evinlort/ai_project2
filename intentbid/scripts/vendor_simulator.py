import argparse
import json
import random
from pathlib import Path

import httpx
from sqlmodel import Session, select

from intentbid.app.db.models import RFO
from intentbid.app.db.session import engine

parser = argparse.ArgumentParser(description="Simulate vendors submitting offers")
parser.add_argument("--api-url", default="http://localhost:8000")
parser.add_argument(
    "--mode",
    choices=["discount", "fast", "warranty", "mixed"],
    default="mixed",
)
parser.add_argument("--limit", type=int, default=5, help="Offers per vendor")
args = parser.parse_args()

vendor_file = Path(__file__).with_name("demo_vendors.json")
if not vendor_file.exists():
    raise SystemExit("Run seed_demo.py first to create demo_vendors.json")

vendors = json.loads(vendor_file.read_text())

with Session(engine) as session:
    rfos = session.exec(select(RFO).where(RFO.status == "OPEN")).all()

if not rfos:
    raise SystemExit("No OPEN RFOs found")

client = httpx.Client(base_url=args.api_url, timeout=5.0)

for vendor in vendors:
    api_key = vendor["api_key"]
    for _ in range(args.limit):
        rfo = random.choice(rfos)
        budget = rfo.constraints.get("budget_max", 150)
        deadline = rfo.constraints.get("delivery_deadline_days", 5)

        if args.mode == "discount":
            price = round(budget * random.uniform(0.6, 0.85), 2)
            eta = min(deadline, random.randint(2, 5))
            warranty = 6
        elif args.mode == "fast":
            price = round(budget * random.uniform(0.85, 1.1), 2)
            eta = max(1, min(deadline, random.randint(1, 2)))
            warranty = 12
        elif args.mode == "warranty":
            price = round(budget * random.uniform(0.9, 1.2), 2)
            eta = min(deadline + 2, random.randint(3, 6))
            warranty = 24
        else:
            price = round(budget * random.uniform(0.7, 1.1), 2)
            eta = min(deadline, random.randint(1, 5))
            warranty = random.choice([6, 12, 18, 24])

        payload = {
            "rfo_id": rfo.id,
            "price_amount": price,
            "currency": "USD",
            "delivery_eta_days": eta,
            "warranty_months": warranty,
            "return_days": random.choice([14, 30, 45]),
            "stock": True,
            "metadata": {"sku": f"SIM-{random.randint(100, 999)}"},
        }

        response = client.post(
            "/v1/offers",
            json=payload,
            headers={"X-API-Key": api_key},
        )
        if response.status_code != 200:
            print(
                f"Offer rejected for vendor {vendor['name']} on RFO {rfo.id}: {response.text}"
            )
        else:
            offer_id = response.json().get("offer_id")
            print(f"Vendor {vendor['name']} posted offer {offer_id} on RFO {rfo.id}")

client.close()
