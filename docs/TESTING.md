# Testing and Definition of Done

A feature is not complete because it renders in the browser. It is complete only when its acceptance tests pass.

## Unit tests
- CSV schema validation.
- Unit conversion (only explicitly supported units).
- Timestamp parsing and timezone handling.
- Duplicate and out-of-order detection.
- Sampling-gap detection.
- Temperature threshold comparison.
- Excursion duration calculations with missing-data caveats.
- Evidence Trust Engine checks.
- State machine transition guards.
- PayPal amount/currency/ID validation.
- Idempotency handling.
- Report content consistency.

## API integration tests
- Create and retrieve shipment.
- Upload valid and invalid CSV.
- Run analysis and retrieve same persisted result.
- Add custody event and preserve order.
- Reject approval when mandatory checks fail.
- Reject capture if reviewer has not approved.
- Reject capture if authorisation is absent/expired/voided.
- Retry capture request without duplicate capture.
- Reject invalid webhook signature.
- Handle PayPal timeout and provider error without showing false success.

## End-to-end tests
1. Clean shipment: create → authorise → upload → analyse → approve → capture.
2. Excursion: create → authorise → upload → analyse → reject → void.
3. Tampered evidence: upload → detect hash/metadata anomaly → review required → capture blocked.
4. Custody gap: upload → detect missing handover → review required.
5. Demo mode: complete same flows with `DEMO-` IDs and persistent simulated label.

## Security checks
- Secrets absent from git history and browser bundle.
- Upload size/type validation and safe storage names.
- CSV formula injection protection in exported CSV.
- Path traversal protection.
- Role/permission checks on reviewer and payment endpoints.
- Rate limits on upload/payment endpoints.
- Webhook signature verification.
- No arbitrary file execution or unsafe document parsing.
- Logs do not expose credentials or sensitive payment details.

## Release checklist
- [ ] Clean install from README works.
- [ ] Database migrations run from empty database.
- [ ] `.env.example` has every required variable and no real secret.
- [ ] Frontend lint/typecheck/build pass.
- [ ] Backend lint/typecheck/tests pass.
- [ ] All P0 acceptance tests pass.
- [ ] PayPal sandbox flow tested end-to-end OR demo mode clearly labelled.
- [ ] All four Sentinel Challenge cases reproduce expected outcomes.
- [ ] No console errors or broken routes in primary flow.
- [ ] Public deployment health check passes.
- [ ] README links and demo video work.
- [ ] Public repo has required license and no secrets.
