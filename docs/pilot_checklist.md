# Pilot Checklist - Hardware Procurement

## Goal

Validate a narrow, high-demand procurement segment (GPUs, memory, SSDs, NICs) with a fast deal cycle and simple integration.

## Target ICP

- Buyers: AI startups, labs, SMB data centers, system integrators, MSPs sourcing GPUs/memory/SSD urgently.
- Vendors: authorized distributors and vetted brokers with inventory, lead time, and traceability docs.

## Key Outcome Metrics (Pilot)

- Time-to-first-quote: <= 2 hours for hot SKUs with at least 3 vendors.
- Award decision time: <= 24 hours for standard requests.
- Quote acceptance rate: >= 20% in pilot.
- Fraud/counterfeit controls: every AWARDED offer has vendor verification plus traceability fields filled.
- Integration time: buyer can post RFQ, receive rankings, and get webhooks in < 30 minutes.

## Onboard 10 Vendors

1) Collect: company name, entity type, regions served, supported categories (GPU/MEMORY/SSD/NIC), and typical lead times.
2) Capture verification artifacts: invoices, serials availability, authorized channel proof, and contact details.
3) Issue vendor API key and confirm they can submit an offer in the sandbox.
4) Record inventory examples (MPN + quantity + condition) and delivery windows.

## Onboard 10 Buyers

1) Collect: target SKUs (MPN), typical quantities, budget ranges, delivery deadlines, and regions.
2) Capture compliance constraints: export control acknowledgement and country restrictions.
3) Provide buyer API key and a minimal RFO template.
4) Validate they can create an RFO and receive a ranking + webhook event.

## Data to Capture (Minimum)

- RFQ: category, line items (MPN, quantity), constraints (budget, deadline, region, incoterms, payment terms), compliance flags.
- Offer: unit price, currency, available quantity, lead time days, condition, warranty months, validity.
- Traceability: authorized channel flag, invoices availability, serials availability, notes.
- Outcomes: time-to-first-quote, award time, acceptance rate, and reasons for rejection.

## Phase 0 Acceptance Criteria

- README includes the Hardware Procurement section with categories, deal-cycle promise, and differentiators.
- Pilot checklist exists with onboarding steps and data capture requirements.
- Acceptance criteria list is documented in this file.
