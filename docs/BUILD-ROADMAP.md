# Build Roadmap

## Phase 0 — Verify constraints (before coding)
- Read the exact hackathon rules and submission checklist.
- Create PayPal developer sandbox app and verify credentials.
- Confirm Orders v2 AUTHORIZE flow works in a minimal test.
- Decide supported CSV schema and sample product profile.
- Lock product scope and avoid claiming regulatory certification.

**Exit gate:** A test order can be created/approved/authorised in sandbox, or a clearly labelled Demo Mode fallback is approved.

## Phase 1 — Working data pipeline
- Create backend project and database models.
- Implement shipment/profile endpoints.
- Implement CSV upload, hashing, parsing, deterministic checks.
- Add passing, excursion, malformed, and custody-gap fixtures.
- Write pytest tests before UI polish.

**Exit gate:** Four fixtures produce stable expected findings.

## Phase 2 — Evidence and review
- Implement Trust Engine with transparent checks.
- Implement custody timeline.
- Implement reviewer queue and state machine.
- Enforce capture guard on backend.

**Exit gate:** No failing/uncertain case can reach capture through API or UI.

## Phase 3 — PayPal
- Implement PayPal adapter and Demo adapter.
- Implement order create, buyer approval, authorisation, capture, void.
- Persist provider IDs/status.
- Implement idempotency and verified webhook reconciliation.

**Exit gate:** Passing sandbox case captures once; rejected case voids; failed API calls never show success.

## Phase 4 — Frontend
- Build overview, shipment detail, upload, temperature graph, evidence findings, custody, review queue, reports.
- Add explicit sandbox/demo mode indicator.
- Add loading/error/empty states and responsive layout.

**Exit gate:** Complete end-to-end flows work without manual database edits.

## Phase 5 — Reports and analytics
- Generate investigation report.
- Add carrier metrics only from persisted shipments and display sample sizes.
- Add AI document extraction only if core tests remain green.

**Exit gate:** Report matches stored facts and clearly distinguishes AI summary from verified data.

## Phase 6 — Submission hardening
- Run all tests, build, typecheck, lint.
- Test public deployment.
- Verify repository, license, environment variables, demo video.
- Rehearse 2–3 minute story: clean → excursion → evidence anomaly → payment consequence.

## Scope protection
If time is short, cut in this order:
1. Live IoT.
2. Predictive alerts.
3. AI extraction.
4. Carrier analytics.
5. Advanced report styling.

Do not cut deterministic checks, human review, payment guardrails, or end-to-end tests.
