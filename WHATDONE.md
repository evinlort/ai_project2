# WHATDONE

This file summarizes the completed MVP scope from WORK.md for this repository.

## Milestones completed
- M0 Bootstrap: FastAPI app with `/health`, Dockerfile, docker-compose, and `scripts/start_dashboard.sh` for local startup.
- M1 DB + migrations: SQLModel models for Vendor, RFO, Offer plus an Alembic initial migration.
- M2 Vendor registration + auth: `/v1/vendors/register` issues an API key (stored hashed); `X-API-Key` auth and `/v1/vendors/me` are implemented.
- M3 RFO API: create RFOs and fetch details with offers count.
- M4 Offer API: submit offers for OPEN RFOs with vendor auth enforcement.
- M5 Ranking endpoint: `/v1/rfo/{id}/best` returns sorted top offers with scoring explain output.
- M6 Dashboard: Jinja2 vendor UI (login, RFO list, RFO detail + submit offer, offers with win/loss); RU UI available under `/ru`.
- M7 Demo scripts: `intentbid/scripts/seed_demo.py` and `intentbid/scripts/vendor_simulator.py` for demo data and offer simulation.
- M8 Tests + docs: pytest suite for API, scoring, dashboard, dockerfile, and start script; README documents setup, curl examples, and config.

## Delivered capabilities
- End-to-end RFO flow: vendor registration, RFO creation, offer submission, and best-offer ranking.
- Rule-based scoring with penalties and weighted components as described in WORK.md.
- Postgres via docker-compose and SQLite by default for local development.
- Database migrations, API documentation via OpenAPI, and basic vendor dashboard.
- Demo workflow support (seed data + simulator) aligned with acceptance criteria.
