# Integration Quickstart (Hardware Procurement)

This quickstart takes you from zero to award locally using the SDK and webhooks.

## Five Commands

```bash
./scripts/start_dashboard.sh
python intentbid/scripts/seed_demo.py
python intentbid/scripts/vendor_simulator.py --api-url http://localhost:8000 --mode mixed --limit 3
export BASE_URL=http://localhost:8000
python examples/buyer_agent.py
```

## 20-Line SDK Flow

```python
from intentbid.sdk import IntentBidClient

base_url = "http://localhost:8000"
client = IntentBidClient(base_url=base_url)

buyer = client.register_buyer("Pilot Buyer")
buyer_key = buyer["api_key"]

rfq = client.create_hardware_rfq(
    category="GPU",
    line_items=[{"mpn": "H100-SXM5-80GB", "quantity": 2}],
    constraints={"budget_max": 200000, "delivery_deadline_days": 7},
    compliance={"export_control_ack": True},
    scoring_profile="balanced",
    buyer_api_key=buyer_key,
)

rfo_id = rfq["rfo_id"]
ranking = client.get_ranking_explain(rfo_id, buyer_api_key=buyer_key)
print("Top offer:", ranking["offers"][0]["offer_id"])
```

## Notes

- Use `/v1/vendors/webhooks` to register a webhook endpoint and receive `rfo.created` and `offer.created` events.
- Hardware award actions require a buyer API key.
