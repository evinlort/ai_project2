# Product framing and terminology alignment

- Add aggregator overview and glossary in docs: Added README aggregator overview sections (EN/RU) with glossary, flow line, and UI/API note, plus a new test to lock the copy.
- Update API documentation copy to reflect the aggregator language: Added API doc tests, updated descriptions to use buyer request/vendor offer wording, and added placeholder docs for list/profile endpoints.
- Align UI copy with buyer request wording without breaking tests: Added template glossary lines in vendor, buyer, and RU templates plus tests for the new buyer request/vendor offer cues.

# Buyer request data model and ownership

- Add tests for buyer-owned request creation: Added coverage for buyer-attached and anonymous RFO creation using the buyer API key header and direct DB assertions.
- Add buyer_id to the RFO model: Added buyer ownership fields/relationships, a migration for the nullable FK/index, and optional buyer attachment in create_rfo routes/services.
- Add explicit buyer request fields for listing and UI: Added persistence tests plus new nullable RFO columns and indexes for title, summary, budget, currency, delivery deadlines, quantity, location, and expires_at.
- Backfill new request columns from existing constraints: Added a legacy-constraints scoring test and an idempotent migration to copy budget/deadline values into the new columns.
- Expose new request fields through schemas: Added schema/validation coverage, expanded RFO create/detail schemas, and wired API creation/detail responses to the new columns.
- Sync request columns with constraints in the service layer: Added constraint-sync tests and a service helper that merges explicit budget/deadline inputs into constraints while storing resolved column values.
- Track awarded offers in the data model: Added award tracking tests plus model/migration updates for awarded_offer_id and offer status/is_awarded fields, and wired award logic to set the winner.
- Add vendor profile storage for matching: Added persistence tests plus a VendorProfile model/table with indexed matching fields for categories, regions, lead times, and minimum order value.

# Aggregator API and service layer

- Add list endpoint for buyer requests with filters: Added list API tests plus list schemas/service/route with status/category/budget/deadline filters and pagination.
- Add buyer-scoped request list endpoint: Added tests and a buyer-owned list route that reuses list_rfos with buyer_id filtering.
- Add vendor-scoped offers list endpoint: Added vendor offer list tests plus schemas, service query, and route returning offer data with request summaries.
- Add buyer-only offers list for a request: Added tests and a buyer-owned offers route returning raw offer data with ownership enforcement.
