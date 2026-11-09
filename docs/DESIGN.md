# UI/UX Design Specification

## Product personality
A calm, high-trust operations console: precise, clinical, modern, and evidence-first. Avoid a generic crypto dashboard or a flashy consumer AI aesthetic.

## Visual direction
- Base: warm off-white or very light cool grey.
- Primary: deep navy/ink.
- Accent: restrained cyan/teal for verified states.
- Warning: amber; critical: red; neutral: slate.
- Use colour plus text/icons; never communicate status by colour alone.
- Typography: highly legible sans-serif; large numeric readings; compact but readable labels.
- Charts must show units, time zone, configured limits, and missing-data gaps.
- Use realistic, restrained visual hierarchy. Avoid tiny text and dense paragraphs.

## Main navigation
1. Overview
2. Shipments
3. Review Queue
4. Carriers
5. Reports
6. Settings / Product Profiles

## Required screens

### 1. Overview
- Active shipments grouped by state: Awaiting evidence, Analysis, Review required, Approved, Rejected, Payment completed.
- Exception summary: excursions, missing records, identity mismatches, custody gaps.
- Recent audit events.
- Clear banner showing `PAYPAL SANDBOX` or `DEMO MODE`.

### 2. Shipment detail
- Shipment ID, product, lot/batch, origin/destination, carrier, expected delivery.
- Product-specific documented storage profile and source/reference.
- Payment state and PayPal order/authorisation identifiers (sandbox only).
- Tabs: Summary, Temperature, Evidence, Custody, Decisions, Audit.

### 3. Upload and analysis
- Drag/drop CSV plus supporting files.
- Show accepted CSV schema and timezone/unit requirements before upload.
- Show parse progress and validation errors.
- Preserve original file metadata and SHA-256.
- Never show a green pass while parsing or checks are incomplete.

### 4. Temperature analysis
- Interactive time-series graph with configured min/max bounds.
- Mark excursions, gaps, duplicates, and out-of-order records.
- Show min/max, duration outside range, count of readings, sampling interval, and data coverage.
- Do not calculate or label MKT unless the product profile explicitly enables it and the calculation implementation has been independently tested and documented.
- Explain that an excursion flag is not a clinical product-disposition decision.

### 5. Evidence Trust Engine
Show separate, explainable checks:
- File hash recorded
- Required columns present
- Valid numeric readings and units
- Timestamp parse and timezone status
- Duplicate timestamps/rows
- Out-of-order readings
- Sampling gaps against configured expected interval
- Sensor/logger ID match
- Calibration document present/validity date (document presence/metadata only; no claim to certify calibration authenticity)
- Shipment ID match
- Chain-of-custody completeness

Do not collapse all of these into an opaque AI score. If a summary score is used, expose the components and label it `Evidence completeness/integrity indicator`, not probability that medicine is safe.

### 6. Chain-of-custody
- Chronological handover events.
- Actor, role, timestamp with timezone, location, event type, notes, evidence attachment.
- Highlight missing expected handovers.
- Demo mode may use seeded sample events; label them as sample data.

### 7. Human review queue
- Shipment findings and original evidence.
- Reviewer identity, decision, reason, timestamp.
- Actions: Approve acceptance conditions, Reject, Request more evidence.
- Approval must require a reason and confirmation.
- Only approved and passing shipments may proceed to capture.
- Reject can trigger void only if an active PayPal authorisation exists and the user confirms.

### 8. Reports
- Export PDF/CSV investigation report.
- Include shipment metadata, profile source, uploaded file hashes, analysis version, findings, chart, custody events, reviewer decision, and payment events.
- Include generated-at time and disclaimer.
- Reports must distinguish source data from AI-generated summaries.

### 9. Carrier analytics
- Aggregate only actual recorded shipments.
- Show sample size and date range.
- Metrics: excursion incidence, evidence completeness failures, custody gaps, delay rate.
- Do not rank carriers on tiny samples; display `insufficient data` below a configurable minimum sample count.

## Interaction principles
- Every status has a plain-language explanation and next action.
- Destructive/payment actions require confirmation.
- Loading, empty, error, and success states must all exist.
- No fake progress bars or fabricated success toasts.
- Responsive desktop-first layout; essential review workflow remains usable on tablet.
- Accessibility: keyboard navigation, visible focus, semantic labels, chart text alternatives, adequate contrast.
