"""Phase 3 authentication, RBAC, outbox events, and user/org security enhancements.

Revision ID: 002
Revises: 001
Create Date: 2026-11-11 12:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    # 1. Database-specific preflight email validation
    if dialect_name == "sqlite":
        # ASCII printable character preflight check (ASCII 33-126) and embedded NUL check
        preflight_query = sa.text("""
            SELECT id, email FROM users
            WHERE trim(email, ' ' || char(9) || char(10) || char(13)) GLOB '*[^!-~]*'
               OR instr(email, char(0)) > 0
        """)
        bad_records = bind.execute(preflight_query).fetchall()
        if bad_records:
            raise ValueError(
                f"SQLite Preflight Migration Error: {len(bad_records)} user record(s) contain "
                f"unsupported non-printable or control characters in their email address: {bad_records[:5]}"
            )
    elif dialect_name == "postgresql":
        # Check for non-ASCII characters in PostgreSQL
        preflight_pg = sa.text("""
            SELECT id, email FROM users
            WHERE email ~ '[^ -~]'
        """)
        bad_records_pg = bind.execute(preflight_pg).fetchall()
        if bad_records_pg:
            raise ValueError(
                f"PostgreSQL Preflight Migration Error: {len(bad_records_pg)} user record(s) contain "
                f"non-ASCII characters: {bad_records_pg[:5]}"
            )

    # 2. Enum migration on PostgreSQL
    if dialect_name == "postgresql":
        # Add MANAGER to user_role enum if not already present
        op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'MANAGER'")

    # 3. Create email backup table to guarantee reversibility of lowercase/trim normalization
    op.create_table(
        "_phase3_email_migration_backup",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("original_email", sa.String(255), nullable=False),
        sa.Column("backed_up_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Backup current emails before normalization
    op.execute("""
        INSERT INTO _phase3_email_migration_backup (user_id, original_email)
        SELECT id, email FROM users
    """)

    # 4. Add token_version to users table for instant session revocation
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("token_version", sa.Integer(), nullable=False, server_default="1"))

    # 5. Add auth_version to organizations table for organization-wide session invalidation
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.add_column(sa.Column("auth_version", sa.Integer(), nullable=False, server_default="1"))

    # 6. Normalize emails (trim whitespace and convert to lowercase)
    op.execute("""
        UPDATE users
        SET email = lower(trim(email, ' ' || char(9) || char(10) || char(13)))
    """ if dialect_name == "sqlite" else """
        UPDATE users
        SET email = lower(trim(email))
    """)

    # 7. Create outbox_events table for reliable event dispatching
    outbox_status_enum = sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", "DEAD_LETTER", name="outbox_status")
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("aggregate_type", sa.String(50), nullable=False),
        sa.Column("aggregate_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON() if dialect_name == "sqlite" else postgresql.JSONB(), nullable=False),
        sa.Column("status", outbox_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("available_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("claim_token", sa.String(36), nullable=True),
        sa.Column("lease_until", sa.DateTime(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_outbox_events_event_type", "outbox_events", ["event_type"])
    op.create_index("ix_outbox_events_aggregate_id", "outbox_events", ["aggregate_id"])
    op.create_index("ix_outbox_events_status", "outbox_events", ["status"])
    op.create_index("ix_outbox_events_available_at", "outbox_events", ["available_at"])
    op.create_index("ix_outbox_events_lease_until", "outbox_events", ["lease_until"])


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    # 1. Drop outbox_events table and its indexes
    op.drop_index("ix_outbox_events_lease_until", table_name="outbox_events")
    op.drop_index("ix_outbox_events_available_at", table_name="outbox_events")
    op.drop_index("ix_outbox_events_status", table_name="outbox_events")
    op.drop_index("ix_outbox_events_aggregate_id", table_name="outbox_events")
    op.drop_index("ix_outbox_events_event_type", table_name="outbox_events")
    op.drop_table("outbox_events")

    if dialect_name == "postgresql":
        op.execute("DROP TYPE IF EXISTS outbox_status")

    # 2. Restore original email values from backup table
    op.execute("""
        UPDATE users
        SET email = (
            SELECT b.original_email
            FROM _phase3_email_migration_backup b
            WHERE b.user_id = users.id
        )
        WHERE users.id IN (SELECT user_id FROM _phase3_email_migration_backup)
    """)

    # 3. Drop backup table
    op.drop_table("_phase3_email_migration_backup")

    # 4. Remove columns added to users and organizations
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("token_version")

    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_column("auth_version")
