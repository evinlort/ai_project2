# Product framing and terminology alignment

## Add aggregator overview and glossary in docs
- Update `README.md` with a short aggregator overview that explains buyer requests and vendor offers.
- Add a glossary mapping: buyer request = RFO, vendor offer = Offer, so API paths stay stable.
- Add a small flow list showing: buyer posts request -> vendors submit offers -> ranking returns best offers.
- Note that the UI will call the same API endpoints used by automation.
---
## Update API documentation copy to reflect the aggregator language
- Review `intentbid/app/api/api_docs.py` descriptions and swap in "buyer request" and "vendor offer" wording.
- Keep existing slugs, paths, and titles that tests rely on (e.g., "Vendor registration").
- Add placeholders for new list/profile endpoints so dashboard docs stay complete as new routes land.
---
## Align UI copy with buyer request wording without breaking tests
- Update template labels in `intentbid/app/templates/*.html` and `intentbid/app/templates/buyer/*.html` to add "Buyer request (RFO)" and "Vendor offer" cues.
- Preserve exact phrases asserted in tests (for example "Create a new RFO" and "Best offers") by keeping them as headings or subheadings.
- Mirror the copy changes in `intentbid/app/templates/ru/*` using consistent Russian terminology.
---
# Buyer request data model and ownership

## Add tests for buyer-owned request creation
- Add pytest coverage to verify `POST /v1/rfo` attaches a buyer when `X-Buyer-API-Key` is provided.
- Add a second test asserting that anonymous request creation still succeeds for backward compatibility.
- Use existing client fixtures to keep the test suite aligned with current patterns.
---
## Add buyer_id to the RFO model
- Update `intentbid/app/db/models.py` to add `buyer_id` with a foreign key to `buyer.id` and a relationship.
- Create an Alembic migration adding the nullable column and index to preserve existing data.
- Ensure the new relationship does not change existing query behavior until it is used.
---
## Add explicit buyer request fields for listing and UI
- Add tests for creating requests with `title`, `summary`, `budget_max`, `currency`, `delivery_deadline_days`, `quantity`, `location`, and `expires_at`.
- Extend the `RFO` model with these nullable columns for indexed search and UI display.
- Create an Alembic migration that adds the columns and indexes without touching existing rows.
- Keep `constraints` for additional request attributes that do not need indexing.
---
## Backfill new request columns from existing constraints
- Add a migration data step that copies `constraints.budget_max` and `constraints.delivery_deadline_days` into the new columns when those columns are null.
- Keep the update idempotent so running migrations twice does not change data.
- Add a small test to ensure scoring still works when only legacy `constraints` are present.
---
## Expose new request fields through schemas
- Update `intentbid/app/core/schemas.py` to add optional fields to `RFOCreate` and `RFODetailResponse`.
- Add validation for non-negative and sensible ranges (for example `budget_max > 0`).
- Keep existing required fields so current tests stay valid.
---
## Sync request columns with constraints in the service layer
- Update `intentbid/app/services/rfo_service.py` so `create_rfo` maps explicit fields into `constraints` for backward compatibility.
- Add a helper to keep `constraints` and new columns aligned on updates.
- Add tests that assert the constraints map is populated from new input fields.
---
## Track awarded offers in the data model
- Add tests to ensure `POST /v1/rfo/{id}/award` can accept an optional `offer_id` and marks the winner.
- Add `awarded_offer_id` to `RFO` and `status`/`is_awarded` fields to `Offer` with migrations.
- Keep existing award behavior intact when `offer_id` is omitted so legacy tests pass.
---
## Add vendor profile storage for matching
- Add tests that create and fetch a vendor profile (categories, regions, lead_time_days, min_order_value).
- Add a `VendorProfile` model or a JSON column on `Vendor` to store the profile payload.
- Create an Alembic migration and add indexes to support matching filters.
---
# Aggregator API and service layer

## Add list endpoint for buyer requests with filters
- Add tests for `GET /v1/rfo` with filters like status, category, budget range, and deadline.
- Create `RFOListItem` and `RFOListResponse` schemas in `intentbid/app/core/schemas.py`.
- Implement the route in `intentbid/app/api/routes_rfo.py` with pagination defaults.
- Add a `list_rfos` service in `intentbid/app/services/rfo_service.py` to encapsulate filtering.
---
## Add buyer-scoped request list endpoint
- Add tests for `GET /v1/buyers/rfos` that ensure only the buyer's requests are returned.
- Add a route to `intentbid/app/api/routes_buyers.py` that requires `X-Buyer-API-Key`.
- Reuse `list_rfos` with a `buyer_id` filter for consistency.
---
## Add vendor-scoped offers list endpoint
- Add tests for `GET /v1/vendors/me/offers` with `X-API-Key` authentication.
- Add a response schema that includes offer data plus a minimal request summary (title, category, status).
- Implement the route in `intentbid/app/api/routes_vendors.py` and a `list_vendor_offers` service helper.
---
## Add buyer-only offers list for a request
- Add tests for `GET /v1/rfo/{id}/offers` that require a buyer key and enforce ownership.
- Create `RFOOffersResponse` schema to return raw offers without ranking.
- Implement the route using existing offer queries with a buyer ownership check.
---
## Allow buyer auth on request creation without breaking existing clients
- Add tests for `POST /v1/rfo` with and without `X-Buyer-API-Key`.
- Add an optional buyer dependency helper in `intentbid/app/api/deps.py`.
- Update `intentbid/app/api/routes_rfo.py` to pass `buyer_id` into `create_rfo` when present.
---
## Add request update endpoint for buyers
- Add tests for `PATCH /v1/rfo/{id}` to allow buyers to update OPEN requests only.
- Add `RFOUpdateRequest` schema with optional fields and validation.
- Implement update logic in `intentbid/app/services/rfo_service.py` and log an audit entry.
---
## Add vendor profile endpoints
- Add tests for `GET /v1/vendors/me/profile` and `PUT /v1/vendors/me/profile`.
- Add request and response schemas for vendor profiles in `intentbid/app/core/schemas.py`.
- Implement profile routes in `intentbid/app/api/routes_vendors.py` with an upsert service function.
---
## Add vendor matching endpoint for requests
- Add tests for `GET /v1/vendors/me/matches` to verify category/region filtering.
- Add a `matching_service.py` with functions that rank or filter requests against the vendor profile.
- Expose match reasons (for example "category_match") in the response schema.
---
## Emit request lifecycle events for automation
- Add tests in `intentbid/tests/test_webhooks.py` for `rfo.created`, `rfo.closed`, and `rfo.awarded` outbox events.
- Call `enqueue_event` from `rfo_service` for create and status transitions.
- Add event documentation entries in `intentbid/app/api/api_docs.py`.
---
## Tighten validation rules for new request fields
- Add tests for invalid inputs (negative budget, empty title, past expires_at).
- Add Pydantic validators in `intentbid/app/core/schemas.py`.
- Keep existing tests green by allowing the legacy constraint-only payload.
---
# UI application that consumes the API

## Add an internal API client wrapper for UI routes
- Add tests for a new UI client using `httpx.ASGITransport` in a dedicated test file.
- Create `intentbid/app/ui/api_client.py` that wraps the SDK or raw httpx calls.
- Provide methods used by the UI: list requests, get request, submit offer, list vendor offers, create request, get best offers, get buyer ranking.
---
## Update vendor login to validate via the API
- Keep existing dashboard login tests and add a new negative-case test for invalid keys.
- Replace direct DB calls in `intentbid/app/api/routes_dashboard.py` and `intentbid/app/api/routes_ru.py` with `GET /v1/vendors/me` through the UI client.
- Preserve cookie behavior so existing UI flows stay intact.
---
## Update vendor request list page to call the request list or match API
- Keep `test_dashboard_rfos_lists_open_rfos` by ensuring the response still contains category text.
- Use `GET /v1/rfo` (or `/v1/vendors/me/matches` once added) in the UI client.
- Add filter inputs (category, budget, deadline) in `intentbid/app/templates/rfos.html` and RU version.
---
## Update vendor request detail page to use API data
- Replace direct DB reads with `GET /v1/rfo/{id}` for request details.
- Pull vendor offers via `GET /v1/vendors/me/offers` and filter by request id.
- Keep the submit-offer form intact while showing request metadata from the API.
---
## Update vendor offer submission to call the API and show validation errors
- Use `POST /v1/offers` with `X-API-Key` in `dashboard_submit_offer`.
- Render validation errors returned by the API in `intentbid/app/templates/rfo_detail.html`.
- Add a test that an invalid offer shows an error message instead of silently redirecting.
---
## Update vendor offers page to use API results and award status
- Replace direct DB and scoring calls with `GET /v1/vendors/me/offers`.
- Show request status and award state in `intentbid/app/templates/offers.html`.
- Keep the "won/lost" visual but map it to `Offer.status` or `is_awarded`.
---
## Add buyer registration page and API key helper
- Add a new route `/buyer/register` that calls `POST /v1/buyers/register` and stores the key in a cookie.
- Create a template that displays the key and next steps for creating a request.
- Add tests to verify the page returns a key and sets the cookie.
---
## Update buyer request creation UI to call the API with new fields
- Replace `create_rfo` calls in `routes_buyer_dashboard.py` with API client calls.
- Expand the form in `intentbid/app/templates/buyer/rfo_new.html` for title, summary, budget, location, quantity, and deadline.
- Keep existing form copy that tests assert ("Create a new RFO").
---
## Add buyer "My requests" UI using the buyer list endpoint
- Add `/buyer/rfos` route that calls `GET /v1/buyers/rfos` using the buyer API key.
- Create a template listing request status, offer counts, and links to best offers.
- Add tests for the new page using a buyer API key.
---
## Update buyer check, best offers, and scoring pages to use API endpoints
- Replace direct service calls with API client calls to `/v1/rfo/{id}`, `/v1/rfo/{id}/best`, and `/v1/buyers/rfo/{id}/ranking`.
- Keep existing headings so tests continue to match expected strings.
- Render API error messages in the existing notice components.
---
## Add an aggregator landing page and shared navigation
- Add a new route in `intentbid/app/main.py` that serves a landing page for buyers and vendors.
- Create a new template with a polished layout, CTA buttons, and clear product explanation.
- Update base templates to include a link to the landing page without removing current nav items.
---
## Keep the RU dashboard in sync with API-driven changes
- Update `intentbid/app/api/routes_ru.py` to use the UI API client for data access.
- Add RU templates for any new pages (buyer register, buyer list, landing).
- Preserve existing RU test strings and URLs.
---
# Automation, docs, and demo data

## Extend the SDK with buyer and request list methods
- Add SDK tests for `register_buyer`, `list_rfos`, `get_rfo`, `list_buyer_rfos`, and `get_buyer_ranking`.
- Implement the methods in `intentbid/sdk/client.py` with correct headers and params.
- Keep existing SDK methods unchanged so current tests keep passing.
---
## Extend the SDK with vendor profile and offer list methods
- Add SDK tests for `get_vendor_profile`, `update_vendor_profile`, `list_vendor_offers`, and `list_matches`.
- Implement the new methods in `intentbid/sdk/client.py`.
- Ensure auth headers use `X-API-Key` consistently.
---
## Update the Postman collection with new endpoints
- Add requests for the new list, profile, match, and update endpoints in `postman/intentbid.postman_collection.json`.
- Keep existing request names intact so prior examples remain valid.
- Add example payloads that include the new request fields.
---
## Update demo data seeding for buyers, requests, and profiles
- Extend `intentbid/scripts/seed_demo.py` to create buyers and attach requests to them.
- Populate new request fields (title, summary, budget, location, deadline) so UI pages look realistic.
- Add vendor profiles with categories and regions for matching demo.
---
## Update the vendor simulator to use list endpoints
- Switch `intentbid/scripts/vendor_simulator.py` to call `GET /v1/rfo` or `/v1/vendors/me/matches` for targets.
- Add CLI flags for category and budget filters to mirror matching behavior.
- Preserve existing modes and defaults so current usage keeps working.
---
## Add an automation guide for robots and agents
- Add a short automation section to `README.md` or a new `AUTOMATION.md`.
- Include curl and SDK examples for listing requests, submitting offers, and fetching rankings.
- Mention rate limits and plan limits from `intentbid/app/core/config.py`.
