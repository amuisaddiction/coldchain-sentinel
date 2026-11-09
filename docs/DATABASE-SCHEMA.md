# Database Schema (proposed)

## `users`
- `id` UUID PK
- `email` unique
- `display_name`
- `role` enum: `BUYER`, `COURIER`, `REVIEWER`, `ADMIN`
- `created_at`

## `shipments`
- `id` UUID PK
- `shipment_ref` unique
- `product_name`, `lot_number`
- `origin`, `destination`, `carrier_name`
- `logger_id`
- `expected_delivery_at`
- `amount_minor`, `currency`
- `status` enum (see ARCHITECTURE)
- `created_by`, `created_at`, `updated_at`

## `product_profiles`
- `id` UUID PK
- `product_name`, `version`
- `min_temp`, `max_temp`, `unit`
- `expected_interval_seconds`
- `max_gap_seconds`
- `timezone_policy`
- `source_reference`, `source_document_id`
- `confirmed_by`, `confirmed_at`
- `effective_from`, `effective_to`
- unique `(product_name, version)`

## `evidence_files`
- `id` UUID PK
- `shipment_id` FK
- `original_filename`, `storage_key`, `mime_type`, `size_bytes`
- `sha256`
- `file_kind` enum: `LOGGER_CSV`, `CALIBRATION_DOC`, `HANDOVER_DOC`, `OTHER`
- `uploaded_by`, `uploaded_at`
- `parse_status`, `metadata_json`

## `temperature_readings`
- `id` UUID PK
- `evidence_file_id` FK
- `timestamp_utc`
- `temperature_value`, `unit`
- `sensor_id`, `shipment_ref`
- `row_number`
- unique only where appropriate; preserve duplicate source rows as findings rather than silently discarding them

## `analysis_runs`
- `id` UUID PK
- `shipment_id` FK
- `profile_id` FK
- `engine_version`, `parser_version`
- `result_status`
- `metrics_json`, `findings_json`
- `created_at`

## `custody_events`
- `id` UUID PK
- `shipment_id` FK
- `event_type`, `actor_id`, `actor_role`
- `occurred_at`, `timezone`, `location_text`
- `notes`, `evidence_file_id`
- `supersedes_event_id` nullable
- `created_at`

## `review_decisions`
- `id` UUID PK
- `shipment_id` FK
- `reviewer_id`
- `decision` enum: `APPROVE`, `REJECT`, `REQUEST_EVIDENCE`
- `reason`
- `created_at`

## `payment_transactions`
- `id` UUID PK
- `shipment_id` FK
- `provider` enum: `PAYPAL`, `DEMO`
- `paypal_order_id`, `authorization_id`, `capture_id`
- `status`, `amount_minor`, `currency`
- `idempotency_key` unique
- `last_provider_response_json`
- `created_at`, `updated_at`

## `audit_events`
- `id` UUID PK
- `actor_id` nullable for system/webhook
- `action`, `entity_type`, `entity_id`
- `occurred_at`
- `reason`
- `metadata_json`
- append-only application policy; restrict update/delete permissions

## Important constraints
- Use integer minor units for money (e.g. paise/cents), never floating point.
- Store timestamps in UTC plus original timezone/source where relevant.
- Never delete source evidence when an analysis is rerun.
- Keep payment IDs and provider status separate from shipment status.
- Enforce state transitions in backend transactions, not only frontend UI.
