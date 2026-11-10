"""001_initial_schema: Initial 12-model relational schema with multi-tenant integrity.

Revision ID: 001
Revises: None
Create Date: 2026-11-10 18:15:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# PostgreSQL native enum definitions
PG_ENUMS = {
    "organization_status": ("ACTIVE", "SUSPENDED", "INACTIVE"),
    "user_role": ("ADMIN", "QUALITY_ASSURANCE", "OPERATOR", "AUDITOR", "VIEWER"),
    "shipment_status": ("CREATED", "IN_TRANSIT", "DELIVERED", "VERIFIED", "FAILED", "CANCELLED"),
    "evidence_type": ("LOGGER_CSV", "CALIBRATION_CERTIFICATE", "DELIVERY_MANIFEST", "INSPECTION_PHOTO"),
    "evidence_integrity_status": ("VERIFIED", "HASH_MISMATCH", "CORRUPTED", "PARSING_FAILED"),
    "temperature_severity": ("NORMAL", "WARNING", "CRITICAL_EXCURSION"),
    "custody_event_type": ("DISPATCH", "AIRPORT_TRANSFER", "CUSTOMS_CLEARANCE", "LAST_MILE_PICKUP", "DELIVERY_HANDOVER"),
    "decision_type": ("PASSED", "FAILED", "MANUAL_REVIEW_REQUIRED"),
    "payment_status": ("AUTHORIZED", "CAPTURED", "VOIDED", "HELD_FOR_REVIEW", "FAILED"),
    "payment_action": ("CAPTURE", "VOID", "REFUND"),
    "idempotency_status": ("IN_PROGRESS", "SUCCESS", "FAILED", "REQUIRES_RECONCILIATION"),
    "investigation_status": ("OPEN", "IN_REVIEW", "RESOLVED_APPROVED", "RESOLVED_REJECTED"),
    "investigation_priority": ("LOW", "MEDIUM", "HIGH", "CRITICAL"),
}


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # In PostgreSQL, create native ENUM types before table definitions
    if is_postgres:
        for enum_name, values in PG_ENUMS.items():
            pg_enum = postgresql.ENUM(*values, name=enum_name, create_type=False)
            pg_enum.create(bind, checkfirst=True)

    # Portable JSON type helper
    json_type = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    # 1. organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "SUSPENDED", "INACTIVE", name="organization_status"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # 2. users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("ADMIN", "QUALITY_ASSURANCE", "OPERATOR", "AUDITOR", "VIEWER", name="user_role"),
            nullable=False,
            server_default="OPERATOR",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("id", "organization_id", name="uq_users_id_org"),
    )
    op.create_index("ix_users_organization_id", "users", ["organization_id"])
    op.create_index("ix_users_email", "users", ["email"])

    # 3. product_profiles
    op.create_table(
        "product_profiles",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("min_temperature_celsius", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("max_temperature_celsius", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("max_excursion_duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expected_sampling_interval_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("max_sampling_gap_seconds", sa.Integer(), nullable=False, server_default="600"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("id", "organization_id", name="uq_product_profile_id_org"),
        sa.UniqueConstraint("organization_id", "name", "version", name="uq_org_product_profile_version"),
        sa.CheckConstraint("min_temperature_celsius < max_temperature_celsius", name="ck_product_profile_temp_range"),
        sa.CheckConstraint("expected_sampling_interval_seconds > 0", name="ck_profile_sampling_interval_positive"),
        sa.CheckConstraint("max_sampling_gap_seconds > 0", name="ck_profile_max_gap_positive"),
        sa.CheckConstraint("max_sampling_gap_seconds >= expected_sampling_interval_seconds", name="ck_profile_gap_gte_interval"),
        sa.CheckConstraint("max_excursion_duration_seconds >= 0", name="ck_profile_excursion_non_negative"),
    )
    op.create_index("ix_product_profiles_organization_id", "product_profiles", ["organization_id"])

    # 4. shipments
    op.create_table(
        "shipments",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_profile_id", sa.String(36), sa.ForeignKey("product_profiles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("tracking_number", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("CREATED", "IN_TRANSIT", "DELIVERED", "VERIFIED", "FAILED", "CANCELLED", name="shipment_status"),
            nullable=False,
            server_default="CREATED",
        ),
        sa.Column("origin", sa.String(255), nullable=False),
        sa.Column("destination", sa.String(255), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("rule_profile_version", sa.Integer(), nullable=False),
        sa.Column("rule_min_temperature_celsius", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("rule_max_temperature_celsius", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("rule_max_excursion_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("rule_expected_sampling_interval_seconds", sa.Integer(), nullable=False),
        sa.Column("rule_max_sampling_gap_seconds", sa.Integer(), nullable=False),
        sa.Column("rule_source_reference", sa.String(255), nullable=False),
        sa.Column("rule_snapshot_json", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tracking_number", name="uq_shipment_tracking_number"),
        sa.UniqueConstraint("id", "organization_id", name="uq_shipments_id_org"),
        sa.ForeignKeyConstraint(
            ["product_profile_id", "organization_id"],
            ["product_profiles.id", "product_profiles.organization_id"],
            name="fk_shipment_product_profile_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_shipment_created_by_org",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("rule_min_temperature_celsius < rule_max_temperature_celsius", name="ck_shipment_rule_temp_range"),
        sa.CheckConstraint("rule_expected_sampling_interval_seconds > 0", name="ck_shipment_rule_sampling_positive"),
        sa.CheckConstraint("rule_max_sampling_gap_seconds > 0", name="ck_shipment_rule_gap_positive"),
        sa.CheckConstraint("rule_max_sampling_gap_seconds >= rule_expected_sampling_interval_seconds", name="ck_shipment_rule_gap_gte_interval"),
        sa.CheckConstraint("rule_max_excursion_duration_seconds >= 0", name="ck_shipment_rule_excursion_non_neg"),
    )
    op.create_index("ix_shipments_organization_id", "shipments", ["organization_id"])
    op.create_index("ix_shipments_product_profile_id", "shipments", ["product_profile_id"])
    op.create_index("ix_shipments_created_by", "shipments", ["created_by"])
    op.create_index("ix_shipments_tracking_number", "shipments", ["tracking_number"])

    # 5. evidence_files
    op.create_table(
        "evidence_files",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("shipment_id", sa.String(36), sa.ForeignKey("shipments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "file_type",
            sa.Enum("LOGGER_CSV", "CALIBRATION_CERTIFICATE", "DELIVERY_MANIFEST", "INSPECTION_PHOTO", name="evidence_type"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column(
            "integrity_status",
            sa.Enum("VERIFIED", "HASH_MISMATCH", "CORRUPTED", "PARSING_FAILED", name="evidence_integrity_status"),
            nullable=False,
            server_default="VERIFIED",
        ),
        sa.Column("uploaded_by", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("parsed_records_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("id", "shipment_id", name="uq_evidence_files_id_shipment"),
        sa.UniqueConstraint("shipment_id", "sha256_hash", name="uq_shipment_evidence_hash"),
        sa.ForeignKeyConstraint(
            ["shipment_id", "organization_id"],
            ["shipments.id", "shipments.organization_id"],
            name="fk_evidence_shipment_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_evidence_uploaded_by_org",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("file_size_bytes > 0", name="ck_evidence_file_size_positive"),
    )
    op.create_index("ix_evidence_files_shipment_id", "evidence_files", ["shipment_id"])
    op.create_index("ix_evidence_files_organization_id", "evidence_files", ["organization_id"])
    op.create_index("ix_evidence_files_uploaded_by", "evidence_files", ["uploaded_by"])
    op.create_index("ix_evidence_files_sha256_hash", "evidence_files", ["sha256_hash"])

    # 6. temperature_readings
    op.create_table(
        "temperature_readings",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("shipment_id", sa.String(36), sa.ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_file_id", sa.String(36), sa.ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("sensor_id", sa.String(100), nullable=False, server_default="PRIMARY"),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("temperature_celsius", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column(
            "severity",
            sa.Enum("NORMAL", "WARNING", "CRITICAL_EXCURSION", name="temperature_severity"),
            nullable=False,
            server_default="NORMAL",
        ),
        sa.Column("sequence_number", sa.Integer(), nullable=True),
        sa.Column("raw_reading_metadata", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["evidence_file_id", "shipment_id"],
            ["evidence_files.id", "evidence_files.shipment_id"],
            name="fk_reading_evidence_shipment",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("evidence_file_id", "row_number", name="uq_reading_evidence_row"),
        sa.CheckConstraint("row_number > 0", name="ck_reading_row_number_positive"),
        sa.CheckConstraint("sequence_number IS NULL OR sequence_number >= 0", name="ck_reading_sequence_non_negative"),
    )
    op.create_index("ix_temp_readings_shipment_id", "temperature_readings", ["shipment_id"])
    op.create_index("ix_temp_readings_evidence_file_id", "temperature_readings", ["evidence_file_id"])
    op.create_index("ix_temp_readings_shipment_time", "temperature_readings", ["shipment_id", "recorded_at"])
    op.create_index("ix_temp_readings_sensor_time", "temperature_readings", ["shipment_id", "sensor_id", "recorded_at"])

    # 7. custody_events
    op.create_table(
        "custody_events",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("shipment_id", sa.String(36), sa.ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evidence_file_id", sa.String(36), nullable=True),
        sa.Column("actor_user_id", sa.String(36), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum("DISPATCH", "AIRPORT_TRANSFER", "CUSTOMS_CLEARANCE", "LAST_MILE_PICKUP", "DELIVERY_HANDOVER", name="custody_event_type"),
            nullable=False,
        ),
        sa.Column("carrier_name", sa.String(255), nullable=False),
        sa.Column("custodian_name", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["shipment_id", "organization_id"],
            ["shipments.id", "shipments.organization_id"],
            name="fk_custody_shipment_org",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_custody_actor_user_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_file_id", "shipment_id"],
            ["evidence_files.id", "evidence_files.shipment_id"],
            name="fk_custody_evidence_shipment",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_custody_events_shipment_id", "custody_events", ["shipment_id"])
    op.create_index("ix_custody_events_organization_id", "custody_events", ["organization_id"])
    op.create_index("ix_custody_events_evidence_file_id", "custody_events", ["evidence_file_id"])
    op.create_index("ix_custody_events_actor_user_id", "custody_events", ["actor_user_id"])

    # 8. verification_decisions
    op.create_table(
        "verification_decisions",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("shipment_id", sa.String(36), sa.ForeignKey("shipments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "decision",
            sa.Enum("PASSED", "FAILED", "MANUAL_REVIEW_REQUIRED", name="decision_type"),
            nullable=False,
        ),
        sa.Column("confidence_score", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("evidence_hash_snapshot", sa.String(64), nullable=False),
        sa.Column("temperature_rule_passed", sa.Boolean(), nullable=False),
        sa.Column("custody_chain_passed", sa.Boolean(), nullable=False),
        sa.Column("sampling_frequency_passed", sa.Boolean(), nullable=False),
        sa.Column("total_excursion_seconds", sa.Integer(), nullable=False),
        sa.Column("max_temperature_detected", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("min_temperature_detected", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("reasoning_summary", sa.Text(), nullable=False),
        sa.Column("decided_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["shipment_id", "organization_id"],
            ["shipments.id", "shipments.organization_id"],
            name="fk_decision_shipment_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["decided_by", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_decision_decided_by_org",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("confidence_score >= 0.000 AND confidence_score <= 1.000", name="ck_decision_confidence_score"),
        sa.CheckConstraint("total_excursion_seconds >= 0", name="ck_decision_excursion_non_negative"),
    )
    op.create_index("ix_verification_decisions_shipment_id", "verification_decisions", ["shipment_id"])
    op.create_index("ix_verification_decisions_organization_id", "verification_decisions", ["organization_id"])
    op.create_index("ix_verification_decisions_decided_by", "verification_decisions", ["decided_by"])

    # 9. payments
    op.create_table(
        "payments",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("shipment_id", sa.String(36), sa.ForeignKey("shipments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("payment_provider", sa.String(32), nullable=False, server_default="PAYPAL"),
        sa.Column("paypal_order_id", sa.String(100), nullable=True),
        sa.Column("paypal_authorization_id", sa.String(100), nullable=True),
        sa.Column("paypal_capture_id", sa.String(100), nullable=True),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("currency_exponent", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("AUTHORIZED", "CAPTURED", "VOIDED", "HELD_FOR_REVIEW", "FAILED", name="payment_status"),
            nullable=False,
            server_default="AUTHORIZED",
        ),
        sa.Column("authorized_at", sa.DateTime(), nullable=True),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("shipment_id", name="uq_payments_shipment_id"),
        sa.ForeignKeyConstraint(
            ["shipment_id", "organization_id"],
            ["shipments.id", "shipments.organization_id"],
            name="fk_payment_shipment_org",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("amount_minor > 0", name="ck_payment_amount_positive"),
        sa.CheckConstraint("currency_exponent >= 0 AND currency_exponent <= 4", name="ck_payment_currency_exponent_range"),
        sa.CheckConstraint("payment_provider IN ('PAYPAL')", name="ck_payment_provider_valid"),
        sa.UniqueConstraint("payment_provider", "paypal_order_id", name="uq_payment_provider_order_id"),
        sa.UniqueConstraint("payment_provider", "paypal_authorization_id", name="uq_payment_provider_auth_id"),
        sa.UniqueConstraint("payment_provider", "paypal_capture_id", name="uq_payment_provider_capture_id"),
    )
    op.create_index("ix_payments_shipment_id", "payments", ["shipment_id"])
    op.create_index("ix_payments_organization_id", "payments", ["organization_id"])
    op.create_index("ix_payments_paypal_order_id", "payments", ["paypal_order_id"])
    op.create_index("ix_payments_paypal_authorization_id", "payments", ["paypal_authorization_id"])
    op.create_index("ix_payments_paypal_capture_id", "payments", ["paypal_capture_id"])

    # 10. payment_idempotency_records
    op.create_table(
        "payment_idempotency_records",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("provider", sa.String(32), nullable=False, server_default="PAYPAL"),
        sa.Column("action", sa.Enum("CAPTURE", "VOID", "REFUND", name="payment_action"), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("payment_id", sa.String(36), sa.ForeignKey("payments.id", ondelete="RESTRICT"), nullable=True),
        sa.Column(
            "status",
            sa.Enum("IN_PROGRESS", "SUCCESS", "FAILED", "REQUIRES_RECONCILIATION", name="idempotency_status"),
            nullable=False,
            server_default="IN_PROGRESS",
        ),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_payload", json_type, nullable=True),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("provider", "action", "idempotency_key", name="uq_payment_idempotency_provider_action_key"),
    )
    op.create_index("ix_payment_idempotency_records_organization_id", "payment_idempotency_records", ["organization_id"])
    op.create_index("ix_payment_idempotency_records_payment_id", "payment_idempotency_records", ["payment_id"])

    # 11. investigations
    op.create_table(
        "investigations",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("shipment_id", sa.String(36), sa.ForeignKey("shipments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assigned_to", sa.String(36), nullable=True),
        sa.Column(
            "status",
            sa.Enum("OPEN", "IN_REVIEW", "RESOLVED_APPROVED", "RESOLVED_REJECTED", name="investigation_status"),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column(
            "priority",
            sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="investigation_priority"),
            nullable=False,
            server_default="MEDIUM",
        ),
        sa.Column("findings", sa.Text(), nullable=True),
        sa.Column("resolution_summary", sa.Text(), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["shipment_id", "organization_id"],
            ["shipments.id", "shipments.organization_id"],
            name="fk_investigation_shipment_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_investigation_assigned_to_org",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_investigations_shipment_id", "investigations", ["shipment_id"])
    op.create_index("ix_investigations_organization_id", "investigations", ["organization_id"])
    op.create_index("ix_investigations_assigned_to", "investigations", ["assigned_to"])

    # 12. audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("shipment_id", sa.String(36), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("payload_before", json_type, nullable=True),
        sa.Column("payload_after", json_type, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_audit_user_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["shipment_id", "organization_id"],
            ["shipments.id", "shipments.organization_id"],
            name="fk_audit_shipment_org",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_audit_events_organization_id", "audit_events", ["organization_id"])
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])
    op.create_index("ix_audit_events_shipment_id", "audit_events", ["shipment_id"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Drop tables in reverse dependency order
    op.drop_table("audit_events")
    op.drop_table("investigations")
    op.drop_table("payment_idempotency_records")
    op.drop_table("payments")
    op.drop_table("verification_decisions")
    op.drop_table("custody_events")
    op.drop_table("temperature_readings")
    op.drop_table("evidence_files")
    op.drop_table("shipments")
    op.drop_table("product_profiles")
    op.drop_table("users")
    op.drop_table("organizations")

    # In PostgreSQL, drop ENUM types after referencing tables are dropped
    if is_postgres:
        for enum_name, values in reversed(list(PG_ENUMS.items())):
            pg_enum = postgresql.ENUM(*values, name=enum_name, create_type=False)
            pg_enum.drop(bind, checkfirst=True)
