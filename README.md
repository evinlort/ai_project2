# IntentBid MVP

IntentBid is a minimal bid/negotiation service for Request for Offer (RFO) workflows. Vendors register, submit offers, and the system ranks the best offers with a transparent, rule-based score.

## Run locally (Docker)

```bash
docker-compose up --build
```

API will be available at `http://localhost:8000`.

## Configuration

Environment variables:

- `DATABASE_URL` (default: `sqlite:///./intentbid.db`)
- `SECRET_KEY` (used for hashing API keys)
- `ENV` (set to `dev` to enable SQL echo)

## Core API

Register a vendor (returns API key once):

```bash
curl -X POST http://localhost:8000/v1/vendors/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme"}'
```

Create an RFO:

```bash
curl -X POST http://localhost:8000/v1/rfo \
  -H "Content-Type: application/json" \
  -d '{
    "category": "sneakers",
    "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
    "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1}
  }'
```

Submit an offer (vendor API key required):

```bash
curl -X POST http://localhost:8000/v1/offers \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <api_key>" \
  -d '{
    "rfo_id": 1,
    "price_amount": 109.99,
    "currency": "USD",
    "delivery_eta_days": 2,
    "warranty_months": 12,
    "return_days": 30,
    "stock": true,
    "metadata": {"sku": "ABC"}
  }'
```

Get top offers:

```bash
curl "http://localhost:8000/v1/rfo/1/best?top_k=3"
```

## Vendor dashboard

Open the vendor console at:

- `http://localhost:8000/dashboard/login`
- or pass `?api_key=...` to `/dashboard/rfos`

## Demo scripts

Seed demo data (creates vendors, RFOs, and offers, and writes vendor API keys to `intentbid/scripts/demo_vendors.json`):

```bash
python intentbid/scripts/seed_demo.py
```

Simulate vendors posting offers via the API:

```bash
python intentbid/scripts/vendor_simulator.py --api-url http://localhost:8000 --mode mixed --limit 3
```

## Tests

```bash
pip install ".[dev]"
pytest
```
