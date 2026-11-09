# ColdChain Sentinel

**Evidence-verified shipment acceptance and payment assurance for temperature-sensitive logistics.**

**Tagline:** Every Degree Matters. Every Payment Must Be Earned.

ColdChain Sentinel connects shipment requirements, temperature records, evidence-integrity checks, chain-of-custody events, human quality review, and PayPal payment actions in one auditable workflow.

> **Important scope boundary:** ColdChain Sentinel is a shipment-evidence and payment-workflow prototype. It does not certify medicine quality, prove biological viability, replace a Qualified Person/quality team, or make regulatory release decisions. A temperature pass means only that the supplied records passed the configured checks. Final product disposition remains with the authorised human quality reviewer.

## What the product does

1. A buyer creates a shipment and records the product's documented storage requirements.
2. The buyer authorises a PayPal sandbox payment (or uses clearly labelled Demo Mode).
3. A courier/operator uploads a temperature logger CSV and supporting evidence.
4. The system validates file structure, timestamps, sensor identity, reading continuity, and configured temperature limits.
5. A deterministic rules engine generates explainable findings and an evidence-integrity assessment.
6. A reviewer can approve, reject, or request more evidence.
7. Only an authorised workflow action can capture or void the PayPal authorisation.
8. The system stores an audit trail and exports an investigation report.

## Core modules

- Shipment workspace and product requirement profile
- Temperature analysis and excursion timeline
- Evidence Trust Engine (integrity and completeness checks)
- Chain-of-custody timeline
- Human review queue and decision record
- PayPal Orders v2 sandbox authorise/capture/void integration
- Evidence/investigation report export
- Carrier performance analytics (based only on recorded shipments)
- Sentinel Challenge demo scenarios

## Project status and honesty

This repository pack is the **implementation specification and starter documentation**, not a claim that the application has already been built or that PayPal credentials/API access have been tested. A feature is considered complete only after its acceptance tests pass in the target environment. Never display a successful payment, shipment verification, or deployment unless the underlying operation actually succeeded.

## Quick start (planned application)

The recommended implementation is a Next.js/TypeScript frontend and Python FastAPI backend. See:
- [`docs/TECH-STACK.md`](docs/TECH-STACK.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/API-AND-PAYPAL-FLOW.md`](docs/API-AND-PAYPAL-FLOW.md)
- [`docs/TESTING.md`](docs/TESTING.md)

The application should support two explicit modes:
- **PayPal Sandbox:** real API calls against PayPal sandbox credentials; payment state comes from PayPal responses.
- **Demo Mode:** deterministic simulated payment states, visibly labelled as simulated. Never mix simulated and sandbox transactions.

## Non-negotiable engineering rules

- AI may extract/explain information; deterministic code makes validation calculations.
- AI must never independently approve medicine quality or trigger payment capture.
- No capture unless all configured acceptance checks pass **and** an authorised human reviewer approves.
- Missing, corrupt, conflicting, or suspicious evidence routes to manual review.
- Preserve the original upload; calculate SHA-256 and record metadata.
- Validate CSV values, timestamps, units, sensor identity, duplicates, gaps, and ordering.
- Product limits must come from an explicitly entered/imported product-specific source; do not invent universal limits.
- Store secrets only in environment variables; never commit `.env`.
- Every payment action must be idempotent and logged.
- A PayPal authorisation is not escrow. Authorisations have time limits; check current PayPal documentation and sandbox behaviour before implementation.

## Suggested build order

1. Data model, shipment creation, CSV parser, deterministic rules engine.
2. Evidence Trust Engine and explainable findings.
3. Chain-of-custody events and reviewer workflow.
4. PayPal sandbox order/authorisation/capture/void flow.
5. Reports, analytics, Sentinel Challenge, UI polish.
6. End-to-end tests and demo rehearsal.

## Hackathon demo

Show one passing shipment, one genuine temperature excursion, one tampered/malformed evidence case, and one incomplete handover. For each, show the exact findings and the resulting workflow. Demonstrate PayPal sandbox capture only for a reviewer-approved passing shipment; demonstrate void for a rejected shipment. Clearly label any simulated transaction.

## License

Choose and add an OSI-approved license (MIT is a simple option) before publishing the public repository. Confirm the hackathon rules' exact license requirement before submission.
