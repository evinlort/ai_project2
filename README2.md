# IntentBid MVP

IntentBid is a minimal Request for Offer (RFO) bidding service. Buyers post requests with constraints and weighted preferences; vendors register, submit offers, and the system scores and ranks them with a transparent rule-based formula. The project includes vendor and buyer dashboards, a small Python SDK, and a webhook outbox for downstream automation.

## Key Features

- Buyer request (RFO) creation with constraints, preferences, and scoring weights.
- Vendor onboarding with API keys, profiles, and offer submission validation.
- Rule-based scoring with explain payloads for auditability.
- Vendor and buyer dashboards (English + Russian UI).
- Webhook outbox for reliable offer.created deliveries.
- Prometheus-style /metrics endpoint with correlation IDs.

## Table of Contents

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [Clone the Repository](#clone-the-repository)
  - [Option A: Docker + Postgres (Recommended)](#option-a-docker--postgres-recommended)
  - [Option B: Local SQLite](#option-b-local-sqlite)
  - [Demo Data and Simulator](#demo-data-and-simulator)
  - [Quick API Smoke Test](#quick-api-smoke-test)
- [Architecture](#architecture)
  - [Directory Structure](#directory-structure)
  - [Request Lifecycle](#request-lifecycle)
  - [Data Flow](#data-flow)
  - [Core Modules and Services](#core-modules-and-services)
  - [Scoring and Ranking](#scoring-and-ranking)
  - [RFO Lifecycle](#rfo-lifecycle)
  - [Access Control](#access-control)
  - [Webhooks and Outbox](#webhooks-and-outbox)
  - [Dashboards (Vendor + Buyer)](#dashboards-vendor--buyer)
  - [SDK](#sdk)
  - [Observability](#observability)
  - [Database Schema (High Level)](#database-schema-high-level)
- [Environment Variables](#environment-variables)
- [Available Scripts](#available-scripts)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Tech Stack

- **Language**: Python 3.11+
- **API**: FastAPI
- **Data layer**: SQLModel + SQLAlchemy
- **Migrations**: Alembic
- **Database**: SQLite (default) or Postgres (Docker)
- **Dashboards**: Jinja2 templates + FastAPI routes
- **HTTP Client**: httpx (server-side and SDK)
- **Testing**: Pytest
- **Containerization**: Docker + Docker Compose

## Prerequisites

- Python 3.11+ (required for local dev)
- pip / venv tooling (venv, virtualenv, or equivalent)
- Docker + Docker Compose (recommended for Postgres and full-stack run)
- Postgres 15+ (only if running without Docker)

## Getting Started

### Clone the Repository

```bash
git clone <repo-url>
cd ai_project2
```

### Option A: Docker + Postgres (Recommended)

This path uses the included `docker-compose.yml` and the startup script to handle the DB, migrations, and API server.

1) Start everything with the helper script:

```bash
./scripts/start_dashboard.sh
```

What it does:
- Starts the Postgres container.
- Waits for the database to be ready (`pg_isready`).
- Builds the API container.
- Runs Alembic migrations (or stamps head if tables already exist).
- Starts the API server.

2) Open the API and docs:

- API root: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health checks: `http://localhost:8000/health`, `http://localhost:8000/ready`

3) Postgres connection details (from `docker-compose.yml`):

- Host: `localhost`
- Port: `15432`
- DB: `intentbid`
- User/Password: `intentbid` / `intentbid`

### Option B: Local SQLite

This path uses a local SQLite database stored in the repo root.

1) Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2) Install dependencies:

```bash
pip install -e .
```

3) Run migrations (uses `DATABASE_URL` or the default SQLite file):

```bash
alembic upgrade head
```

4) Start the API server:

```bash
uvicorn intentbid.app.main:app --reload --host 0.0.0.0 --port 8000
```

The default SQLite database file is `./intentbid.db` (set by `DATABASE_URL` in `intentbid.app.core.config`).

### Demo Data and Simulator

Seed demo vendors, buyers, RFOs, and offers (also writes demo keys to JSON files):

```bash
python intentbid/scripts/seed_demo.py
```

This generates:
- `intentbid/scripts/demo_vendors.json`
- `intentbid/scripts/demo_buyers.json`

Simulate vendors posting offers (requires OPEN RFOs and demo keys):

```bash
python intentbid/scripts/vendor_simulator.py --api-url http://localhost:8000 --mode mixed --limit 3
```

Docker equivalents:

```bash
docker-compose run --rm api python intentbid/scripts/seed_demo.py
docker-compose run --rm api python intentbid/scripts/vendor_simulator.py --api-url http://localhost:8000 --mode mixed --limit 3
```

### Quick API Smoke Test

Register a vendor (returns a one-time API key):

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

Submit an offer (use the vendor API key from registration):

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

Fetch the best offers with scoring explain:

```bash
curl "http://localhost:8000/v1/rfo/1/best?top_k=3"
```

If you want RFOs tied to a specific buyer, register a buyer and send `X-Buyer-API-Key`:

```bash
curl -X POST http://localhost:8000/v1/buyers/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Buyer Inc"}'

curl -X POST http://localhost:8000/v1/rfo \
  -H "Content-Type: application/json" \
  -H "X-Buyer-API-Key: <buyer_key>" \
  -d '{
    "category": "laptop",
    "constraints": {"budget_max": 900, "delivery_deadline_days": 5},
    "preferences": {"w_price": 0.5, "w_delivery": 0.3, "w_warranty": 0.2}
  }'
```

Postman collection: `postman/intentbid.postman_collection.json`.

## Architecture

### Directory Structure

```
.
├── intentbid/
│   ├── app/
│   │   ├── api/                 # FastAPI routers
│   │   ├── core/                # config, scoring, observability, security
│   │   ├── db/                  # models, session, migrations
│   │   ├── services/            # business logic (RFO, offers, billing, webhooks)
│   │   ├── templates/           # Jinja2 templates (English + Russian)
│   │   └── ui/                  # async API client for dashboards
│   ├── sdk/                     # Python SDK client
│   └── scripts/                 # demo data and simulator
├── scripts/start_dashboard.sh   # Docker startup helper
├── docker-compose.yml           # API + Postgres stack
├── Dockerfile                   # API container image
├── alembic.ini                  # Alembic config
├── pyproject.toml               # dependencies + pytest config
└── postman/intentbid.postman_collection.json
```

### Request Lifecycle

1) Incoming HTTP request hits FastAPI in `intentbid/app/main.py`.
2) Middleware logs the request, assigns `X-Correlation-Id`, and records metrics.
3) Router dispatches to a handler (e.g., `/v1/rfo`, `/v1/offers`).
4) Handler uses a SQLModel `Session` (from `intentbid/app/db/session.py`).
5) Service layer performs validation, updates models, and commits.
6) Response is serialized via Pydantic schemas and returned.

### Data Flow

**Vendor offer flow**

```
Vendor registers -> receives API key
Vendor submits offer -> validation -> Offer stored -> EventOutbox + UsageEvent recorded
Scoring service reads Offer + RFO -> returns ranked results
```

**Buyer ranking flow**

```
Buyer registers -> receives buyer API key
Buyer fetches ranking -> Offer + RFO scored -> explain payload returned
```

### Core Modules and Services

- `intentbid/app/main.py`: FastAPI app, dashboards, health/ready/metrics endpoints.
- `intentbid/app/api/*`: REST endpoints for vendors, buyers, RFOs, offers, dashboards.
- `intentbid/app/core/config.py`: Pydantic settings with `.env` support.
- `intentbid/app/core/scoring.py`: Rule-based scoring with explain payloads.
- `intentbid/app/core/observability.py`: request logging, correlation IDs, metrics.
- `intentbid/app/db/models.py`: SQLModel schemas (Vendor, Buyer, RFO, Offer, etc.).
- `intentbid/app/services/*`: business logic (RFO transitions, billing caps, webhooks).
- `intentbid/app/ui/api_client.py`: async API client used by dashboards.
- `intentbid/sdk/client.py`: synchronous SDK for automation and bots.

### Scoring and Ranking

Scoring is intentionally transparent (see `intentbid/app/core/scoring.py`):

- Hard filters (score = 0):
  - `price_amount > budget_max`
  - `stock == false`
  - `delivery_eta_days > delivery_deadline_days`
- Normalized components:
  - `price_score = clamp01(1 - price_amount / budget_max)`
  - `delivery_score = clamp01(1 - delivery_eta_days / delivery_deadline_days)`
  - `warranty_score = clamp01(warranty_months / 24)`
- Final score uses weights from `rfo.weights` or falls back to `rfo.preferences`:
  - defaults: `w_price=0.5`, `w_delivery=0.3`, `w_warranty=0.2`

The `/v1/rfo/{id}/best` and `/v1/buyers/rfo/{id}/ranking` endpoints return an `explain` payload with component scores, weights, and penalties.

### RFO Lifecycle

RFOs transition through these states (see `intentbid/app/services/rfo_service.py`):

```
OPEN -> CLOSED -> AWARDED
```

Endpoints:
- `POST /v1/rfo/{id}/close`
- `POST /v1/rfo/{id}/award` (optionally set `offer_id`)
- `POST /v1/rfo/{id}/reopen` (returns to OPEN from CLOSED)

Each transition writes to `audit_log` for traceability.

### Access Control

- Vendor endpoints use `X-API-Key` (hashed via HMAC with `SECRET_KEY`).
- Buyer endpoints use `X-Buyer-API-Key`.
- API keys are generated once and stored hashed in the database.
- `VendorApiKey` and `BuyerApiKey` track `last_used_at` and revocation.
- Public endpoints include `POST /v1/rfo`, `GET /v1/rfo`, `GET /v1/rfo/{id}`, and scoring views such as `GET /v1/rfo/{id}/best`.
- RFO status/scoring updates currently do not enforce auth (`/close`, `/award`, `/reopen`, `/scoring`); consider adding guards if you need stricter controls.

### Webhooks and Outbox

- Vendor webhooks are registered via `POST /v1/vendors/webhooks`.
- `EventOutbox` records `offer.created` and `rfo.*` events.
- `dispatch_outbox` (in `intentbid/app/services/webhook_service.py`) delivers events with retries and exponential backoff.

Note: A dedicated background worker is not included. To deliver webhooks in production, run `dispatch_outbox` on a schedule (cron, worker, or task queue).

### Dashboards (Vendor + Buyer)

Dashboards are server-rendered via Jinja2 templates under `intentbid/app/templates`.

**Vendor dashboard (English)**
- Login: `http://localhost:8000/dashboard/login`
- RFO list: `http://localhost:8000/dashboard/rfos`
- RFO detail + submit offer: `http://localhost:8000/dashboard/rfos/<id>`
- Offers: `http://localhost:8000/dashboard/offers`
- API cards: `http://localhost:8000/dashboard/apis`

**Buyer dashboard (English)**
- Register buyer key: `http://localhost:8000/buyer/register`
- Create RFO: `http://localhost:8000/buyer/rfos/new`
- Check RFO: `http://localhost:8000/buyer/rfos/check`
- Best offers: `http://localhost:8000/buyer/rfos/best`
- Scoring view: `http://localhost:8000/buyer/rfos/scoring`

**Russian UI**
- Russian landing + dashboards are prefixed with `/ru` (e.g., `/ru/dashboard/login`).

### SDK

The Python SDK wraps common API calls (see `intentbid/sdk/client.py`).

```python
from intentbid.sdk import IntentBidClient

client = IntentBidClient(base_url="http://localhost:8000", api_key="<vendor_key>")
rfos = client.list_rfos(status="OPEN", limit=5)
client.submit_offer({
    "rfo_id": 1,
    "price_amount": 109.99,
    "currency": "USD",
    "delivery_eta_days": 2,
    "warranty_months": 12,
    "return_days": 30,
    "stock": True,
    "metadata": {"sku": "ABC"},
})
```

### Observability

- `GET /metrics` exposes an in-memory Prometheus-style counter of HTTP requests.
- `X-Correlation-Id` is added to responses for traceability.
- Request logs include method, path, status, duration, and redacted auth headers.
- Metrics are stored in memory and reset when the API process restarts.

### Database Schema (High Level)

Core tables (see `intentbid/app/db/models.py` and Alembic migrations):

- **vendor**: vendor identity + legacy api_key_hash
- **vendor_api_key**: rotating API keys with status/last_used_at
- **vendor_profile**: categories, regions, lead time, minimum order value
- **vendor_webhook**: webhook URL, secret, last delivery
- **buyer**: buyer identity
- **buyer_api_key**: buyer API keys and status
- **rfo**: buyer request with constraints, preferences, status, scoring
- **offer**: vendor offers for RFOs
- **audit_log**: RFO transition audit trail
- **event_outbox**: pending/delivered webhook events
- **subscription / plan_limit / usage_event**: billing and monthly caps

## Environment Variables

The app uses Pydantic settings with `.env` support (see `intentbid/app/core/config.py`).

### Required (Production)

| Variable | Description | Example |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg://intentbid:intentbid@db:5432/intentbid` |
| `SECRET_KEY` | HMAC secret for API key hashing | `change-me` |

### Optional (Defaults Shown)

| Variable | Description | Default |
| --- | --- | --- |
| `ENV` | Environment name (controls SQL echo) | `dev` |
| `MAX_OFFERS_PER_VENDOR_RFO` | Max offers a vendor can submit per RFO | `5` |
| `OFFER_COOLDOWN_SECONDS` | Cooldown between offers per vendor/RFO | `0` |

Notes:
- `ENV=dev` enables SQL echo in SQLModel engine creation.
- When using SQLite, the default database is `sqlite:///./intentbid.db`.
- Create a `.env` file at repo root to avoid exporting variables manually.

## Available Scripts

| Command | Description |
| --- | --- |
| `./scripts/start_dashboard.sh` | Start Postgres + run migrations + launch API (Docker) |
| `docker-compose up --build` | Start API + DB containers |
| `docker-compose run --rm api alembic upgrade head` | Run migrations in Docker |
| `python intentbid/scripts/seed_demo.py` | Seed demo vendors, buyers, RFOs, offers |
| `python intentbid/scripts/vendor_simulator.py --api-url http://localhost:8000 --mode mixed --limit 3` | Simulate vendor offer submissions |
| `uvicorn intentbid.app.main:app --reload` | Start API server (local) |
| `alembic upgrade head` | Run migrations (local) |
| `pytest` | Run test suite |

## Testing

Install dev dependencies and run tests:

```bash
pip install ".[dev]"
pytest
```

Tests live under `intentbid/tests` and cover APIs, dashboards, migrations, and scoring behavior.

## Deployment

### Docker Image

Build the container image:

```bash
docker build -t intentbid .
```

Run the API (ensure Postgres is reachable):

```bash
docker run --rm -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg://intentbid:intentbid@<db-host>:5432/intentbid \
  -e SECRET_KEY=change-me \
  -e ENV=prod \
  intentbid
```

### Migrations in Production

Run Alembic migrations as part of your deploy:

```bash
docker run --rm \
  -e DATABASE_URL=postgresql+psycopg://intentbid:intentbid@<db-host>:5432/intentbid \
  -e SECRET_KEY=change-me \
  intentbid alembic upgrade head
```

### Recommended Production Notes

- Use Postgres rather than SQLite.
- Set a strong `SECRET_KEY` (never use the dev default).
- Run `dispatch_outbox` on a schedule if you rely on webhooks.
- Add a process manager (systemd, ECS, Kubernetes, etc.) for restarts and logs.

## Troubleshooting

**Database connection refused**

- Confirm the DB container is running: `docker ps`.
- Check `DATABASE_URL` and port mapping (`15432` for local compose).
- Ensure Postgres accepts connections from the API container.

**Migrations fail with duplicate tables**

- The helper script already handles this by stamping Alembic head.
- Manual fix:

```bash
alembic stamp head
```

**401 Unauthorized on vendor/buyer endpoints**

- Ensure you are sending the correct header:
  - Vendor: `X-API-Key: <vendor_key>`
  - Buyer: `X-Buyer-API-Key: <buyer_key>`

**Vendor simulator says no OPEN RFOs**

- Create an RFO first or run `seed_demo.py` to generate sample data.

**429 Plan limit exceeded**

- The billing system enforces per-plan monthly offer caps.
- Check `subscription`, `plan_limit`, and `usage_event` records in the database.

## Contributing

1) Create a feature branch.
2) Add or update tests where behavior changes.
3) Run `pytest` before opening a PR.

## License

No license file is included in this repository. Add a `LICENSE` file if you intend to distribute or open-source the project.
