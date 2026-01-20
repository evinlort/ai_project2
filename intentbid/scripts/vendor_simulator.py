import argparse
import json
import random
from pathlib import Path

import httpx

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
client = httpx.Client(base_url=args.api_url, timeout=5.0)

list_response = client.get("/v1/rfo", params={"status": "OPEN", "limit": 50})
list_response.raise_for_status()
open_rfos = list_response.json().get("items", [])

if not open_rfos:
    raise SystemExit("No OPEN RFOs found via API")

for vendor in vendors:
    api_key = vendor["api_key"]
    match_response = client.get(
        "/v1/vendors/me/matches",
        headers={"X-API-Key": api_key},
        params={"limit": 50},
    )
    if match_response.status_code == 200:
        match_items = match_response.json().get("items", [])
        candidate_rfos = [item["rfo"] for item in match_items]
    else:
        candidate_rfos = []

    if not candidate_rfos:
        candidate_rfos = open_rfos

    for _ in range(args.limit):
        rfo = random.choice(candidate_rfos)
        budget = rfo.get("budget_max") or 150
        deadline = rfo.get("delivery_deadline_days") or 5

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
            "rfo_id": rfo["id"],
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
                f"Offer rejected for vendor {vendor['name']} on RFO {rfo['id']}: {response.text}"
            )
        else:
            offer_id = response.json().get("offer_id")
            print(f"Vendor {vendor['name']} posted offer {offer_id} on RFO {rfo['id']}")

client.close()
