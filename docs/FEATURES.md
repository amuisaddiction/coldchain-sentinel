# Feature Specification and Acceptance Criteria

## P0 — Required for hackathon MVP

### F01. Shipment creation
Fields: shipment reference, product, lot/batch, origin, destination, carrier, expected delivery, logger ID, product profile, buyer, amount/currency.
Acceptance:
- Required fields validated server-side.
- Unique shipment reference enforced.
- Shipment can be opened again after refresh.
- Invalid data returns actionable errors.

### F02. Product storage profile
Fields: min/max temperature, unit, expected sample interval, timezone policy, allowed data-gap threshold, source document/reference, effective dates, reviewer confirmation.
Acceptance:
- No default universal medicine limits.
- Profile source and author are stored.
- Changes are versioned and do not silently rewrite historical analyses.

### F03. CSV ingestion
Initial supported schema: `timestamp,temperature,unit,sensor_id,shipment_id`.
Acceptance:
- Accept documented CSV format and show schema guidance.
- Reject missing required columns, invalid units, non-numeric readings, impossible timestamps, and empty files.
- Handle timezone explicitly; do not silently assume local time.
- Preserve original file and SHA-256.
- Report duplicate/out-of-order rows and gaps.
- Large uploads have size/row limits and clear error messages.

### F04. Deterministic temperature analysis
Acceptance:
- Compare each valid reading to the shipment's configured profile.
- Compute min/max, count, coverage, out-of-range readings, duration outside range where data permits.
- Mark unknown periods caused by missing data; never interpolate them as measured facts.
- Return machine-readable findings and human-readable explanations.
- Analysis is reproducible for same input, profile version, and engine version.

### F05. Evidence Trust Engine
Acceptance:
- Check file hash, schema, sensor/shipment identity, duplicate/out-of-order readings, configured gaps, missing metadata, and calibration-document metadata.
- Each check returns `PASS`, `WARN`, `FAIL`, or `NOT_CHECKED`, plus evidence and explanation.
- A hash detects later file changes but does not prove the source logger or original data was authentic.
- Do not claim cryptographic tamper-proofing or sensor authenticity without a trusted signing mechanism.

### F06. Chain-of-custody
Acceptance:
- Record handover actor, role, event, timestamp/timezone, location, and optional attachment.
- Events are append-only in the application workflow; corrections create a superseding event with reason.
- Missing expected handovers become findings.
- Demo events are visibly identified as seeded/demo data.

### F07. Review workflow
States: `DRAFT`, `AWAITING_PAYMENT_AUTH`, `AWAITING_EVIDENCE`, `ANALYZING`, `REVIEW_REQUIRED`, `APPROVED`, `REJECTED`, `CAPTURE_PENDING`, `CAPTURED`, `VOID_PENDING`, `VOIDED`, `PAYMENT_ERROR`.
Acceptance:
- Only authorised reviewer role can approve/reject.
- Approval requires all mandatory checks to pass and a written reason.
- Warnings may require explicit reviewer acknowledgement.
- Any failure or uncertain evidence blocks automatic capture.
- All transitions are validated server-side and audited.

### F08. PayPal sandbox integration
Acceptance:
- Create PayPal order with `intent=AUTHORIZE`.
- Complete buyer approval in PayPal sandbox.
- Authorise order and persist PayPal IDs/status.
- Capture only after passing checks and authorised reviewer approval.
- Void an active authorisation after rejection, with confirmation.
- Handle API errors, duplicate requests, timeouts, retries, and idempotency.
- Verify webhook signatures before trusting webhook events.
- Display PayPal's actual returned status; never infer success from an HTTP request being sent.
- If credentials or account permissions are unavailable, app clearly uses Demo Mode; never label simulation as PayPal.

### F09. Investigation report
Acceptance:
- Export a report with original-file hash, profile version/source, findings, chart, custody timeline, reviewer decision, payment events, timestamps, and disclaimer.
- Report generation failure is visible and retryable.
- Report values match stored analysis records.

### F10. Sentinel Challenge
Seed four reproducible scenarios:
1. Clean shipment: checks pass; reviewer approves; sandbox capture or clearly labelled simulated capture.
2. Temperature excursion: fail configured limit; capture blocked; reviewer rejects; sandbox void or simulated void.
3. Evidence anomaly: missing timestamps / duplicate rows / mismatched sensor ID; review required; no capture.
4. Custody gap: missing handover; review required; no capture.
Acceptance:
- One-click reset restores deterministic sample scenarios.
- Each scenario has expected result tests.
- Demo data never contaminates real shipment analytics.

## P1 — Only after P0 is stable
- Carrier reliability analytics with sample-size warnings.
- AI document extraction with source-linked fields and reviewer confirmation.
- Multi-file evidence bundles.
- PDF report styling and CSV export.
- Role-based buyer, courier, reviewer views.

## P2 — Future work, not hackathon claims
- Live IoT sensor integration.
- Predictive excursion alerts.
- External calibration registry validation.
- Regulatory integrations.
- Automated product disposition or medicine viability assessment (out of scope without qualified validation).
