# WHATDONE

This file summarizes the completed work for the IntentBid MVP in this repository.

## Milestones completed
- M0 Bootstrap: FastAPI app with `/health`, Dockerfile, docker-compose, and `scripts/start_dashboard.sh` for local startup.
- M1 DB + migrations: SQLModel models for vendors, buyers, RFOs, offers, webhooks/outbox, billing tables, and Alembic migrations.
- M2 Vendor registration + auth: `/v1/vendors/register` issues hashed API keys; `X-API-Key` auth, `/v1/vendors/me`, key rotation/revocation, onboarding status.
- M3 RFO API: create RFOs, fetch details with offer counts, and manage status transitions with audit logging.
- M4 Offer API: submit offers for OPEN RFOs with validation (price/ETA/warranty/return), per-RFO caps, cooldowns, plan limits, and usage tracking.
- M5 Ranking endpoints: `/v1/rfo/{id}/best` returns top offers with explain output; buyer ranking returns every offer with explain data.
- M6 Dashboards: vendor Jinja2 UI (login, RFO list, RFO detail + submit offer, offers with win/loss) plus RU UI; buyer console for RFO create/check/best/scoring.
- M7 Demo scripts: `intentbid/scripts/seed_demo.py` and `intentbid/scripts/vendor_simulator.py` for demo data and offer simulation.
- M8 Tests + docs: pytest suite for API, scoring, dashboards, buyer flows, and SDK; README/HOWTO updates; dashboard API reference pages; Postman collection; Python SDK.
- M9 Webhooks + dispatch: vendor webhook registration, outbox delivery with retries, signatures, and last-delivery tracking.
- M10 Scoring extensibility: scoring config updates and ranking explain endpoints with version/weight/penalty details.
- M11 Observability + ops: `/metrics` and `/ready` endpoints, correlation IDs + request logging, CI workflow, and template packaging in `pyproject.toml`.

## Delivered capabilities
- End-to-end vendor and buyer RFO lifecycle with transparent scoring and ranking.
- Buyer and vendor authentication flows with hashed API keys and dashboard cookie helpers.
- Operational guardrails: plan limits, per-RFO caps, cooldowns, usage events, and webhook dispatch.
- Documentation/tooling: API docs pages under `/dashboard/apis` and `/ru/dashboard/apis`, Python SDK client, Postman collection, and setup guides.
