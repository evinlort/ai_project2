# Product framing and terminology alignment

- Add aggregator overview and glossary in docs: Added README aggregator overview sections (EN/RU) with glossary, flow line, and UI/API note, plus a new test to lock the copy.
- Update API documentation copy to reflect the aggregator language: Added API doc tests, updated descriptions to use buyer request/vendor offer wording, and added placeholder docs for list/profile endpoints.
- Align UI copy with buyer request wording without breaking tests: Added template glossary lines in vendor, buyer, and RU templates plus tests for the new buyer request/vendor offer cues.

# Buyer request data model and ownership

- Add tests for buyer-owned request creation: Added coverage for buyer-attached and anonymous RFO creation using the buyer API key header and direct DB assertions.
- Add buyer_id to the RFO model: Added buyer ownership fields/relationships, a migration for the nullable FK/index, and optional buyer attachment in create_rfo routes/services.
- Add explicit buyer request fields for listing and UI: Added persistence tests plus new nullable RFO columns and indexes for title, summary, budget, currency, delivery deadlines, quantity, location, and expires_at.
