# Security, Safety, and Claims Boundaries

## Data and upload security
- Treat every uploaded CSV/PDF/image as untrusted.
- Restrict file size, row count, MIME/type, and parsing time.
- Store files under generated IDs, not user-supplied paths.
- Keep original bytes read-only after ingestion.
- Calculate SHA-256 and retain it with upload metadata.
- Sanitize exported CSV cells to prevent spreadsheet formula injection.
- Do not put secrets or personal data in logs.

## Payment safety
- Keep PayPal secret on backend only.
- Require server-side reviewer authorisation for capture.
- Validate amount, currency, order ID, authorisation ID, shipment ID, and current state.
- Use idempotency keys and safe retry rules.
- Verify webhook signatures.
- Separate void (uncaptured authorisation) from refund (captured payment).
- Never claim escrow or guaranteed instant release of a bank hold.

## Evidence limitations
- Hashing proves whether the stored file changed after hashing; it does not prove the original data was truthful.
- CSV metadata can be forged.
- A logger ID match is not cryptographic sensor authentication.
- Calibration document presence is not proof the certificate is genuine or the sensor was correctly used.
- Missing data means unknown conditions, not proof of a breach or proof of compliance.
- A temperature reading inside range does not alone establish product viability.

## Medical and regulatory claims
- Product-specific limits must be sourced and confirmed by an authorised quality professional.
- No universal temperature range or MKT threshold is safe to assume for all medicines.
- MKT may be inappropriate for certain products; only use where a documented product-specific method authorises it.
- The app does not provide medical advice, certify product quality, or replace GDP/GMP/regulatory quality systems.
- Final product disposition is a human quality decision outside the prototype's authority.

## Public demo privacy
- Use synthetic shipment and logger data.
- Do not upload patient information, real shipment identifiers, or real payment credentials.
