"""Alembic migration lifecycle and PostgreSQL dialect DDL compilation tests."""

import os
from pathlib import Path
import sqlite3
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

from app.core.database import Base
import app.models  # Ensure all 12 models are registered


@pytest.fixture
def test_alembic_config(tmp_path):
    """Generates an Alembic Config pointing to a temporary test SQLite database."""
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    test_db_path = tmp_path / "test_migration.db"
    test_db_url = f"sqlite:///{test_db_path.as_posix()}"

    config = Config(str(ini_path))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", test_db_url)
    return {"config": config, "db_path": test_db_path}


def test_sqlite_migration_lifecycle(test_alembic_config):
    """Verify clean execution of upgrade -> downgrade -> upgrade on SQLite."""
    cfg = test_alembic_config["config"]
    db_path = test_alembic_config["db_path"]

    # 1. Upgrade to head
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()

    expected_tables = {
        "organizations",
        "users",
        "product_profiles",
        "shipments",
        "evidence_files",
        "temperature_readings",
        "custody_events",
        "verification_decisions",
        "payments",
        "payment_idempotency_records",
        "investigations",
        "audit_events",
        "alembic_version",
    }
    assert expected_tables.issubset(set(tables))

    # 2. Downgrade to base
    command.downgrade(cfg, "base")

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    post_down_tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()

    # User tables should be completely dropped; only alembic_version might remain or empty
    remaining_user_tables = set(post_down_tables).intersection(expected_tables - {"alembic_version"})
    assert len(remaining_user_tables) == 0

    # 3. Upgrade back to head
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    final_tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()

    assert expected_tables.issubset(set(final_tables))


def test_postgresql_ddl_compilation():
    """
    Offline compilation of all 12 model DDL statements against the PostgreSQL dialect.

    IMPORTANT ARCHITECTURAL NOTICE:
    Offline PostgreSQL DDL compilation verifies SQLAlchemy schema syntax generation against
    the PostgreSQL dialect, but does NOT verify live PostgreSQL execution, foreign key locking
    behavior, or migration execution on a running server.
    Live PostgreSQL runtime compatibility is UNVERIFIED on host due to the absence of a local PostgreSQL instance.
    """
    pg_dialect = postgresql.dialect()
    compiled_ddl = {}

    for table_name, table in Base.metadata.tables.items():
        create_stmt = str(CreateTable(table).compile(dialect=pg_dialect)).strip()
        assert len(create_stmt) > 0
        assert f"CREATE TABLE {table_name}" in create_stmt
        compiled_ddl[table_name] = create_stmt

    # Verify all baseline and extended tables compiled to PostgreSQL syntax
    assert len(compiled_ddl) >= 12

    # Verify PostgreSQL specific features compiled correctly
    shipments_ddl = compiled_ddl["shipments"]
    assert "JSONB" in shipments_ddl or "jsonb" in shipments_ddl.lower()
    assert "fk_shipment_product_profile_org" in shipments_ddl

    evidence_ddl = compiled_ddl["evidence_files"]
    assert "fk_evidence_shipment_org" in evidence_ddl
    assert "fk_evidence_uploaded_by_org" in evidence_ddl

    payments_ddl = compiled_ddl["payments"]
    assert "amount_minor BIGINT" in payments_ddl or "BIGINT" in payments_ddl
    assert "ck_payment_amount_positive" in payments_ddl


def test_postgresql_migration_enum_idempotency():
    """
    Simulates Alembic 001 and 002 upgrade & downgrade on PostgreSQL to verify:
    1. Idempotent DO $$ blocks with IF NOT EXISTS checks for all 13 initial PG enums.
    2. Zero duplicate CREATE TYPE statements emitted by create_table.
    3. Idempotent outbox_status enum creation in 002.
    4. Clean downgrade with DROP TYPE IF EXISTS ... CASCADE.
    """
    import importlib.util
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from alembic import op

    backend_dir = Path(__file__).resolve().parent.parent
    ver_dir = backend_dir / "alembic" / "versions"

    spec_001 = importlib.util.spec_from_file_location("mig_001", ver_dir / "001_initial_schema.py")
    mig_001 = importlib.util.module_from_spec(spec_001)
    spec_001.loader.exec_module(mig_001)

    spec_002 = importlib.util.spec_from_file_location("mig_002", ver_dir / "002_phase3_auth_rbac.py")
    mig_002 = importlib.util.module_from_spec(spec_002)
    spec_002.loader.exec_module(mig_002)

    recorded_statements = []

    def mock_executor(sql, *args, **kwargs):
        if hasattr(sql, "compile"):
            stmt_str = str(sql.compile(dialect=postgresql.dialect())).strip()
        else:
            stmt_str = str(sql).strip()
        recorded_statements.append(stmt_str)

    engine = sa.create_mock_engine("postgresql://", mock_executor)
    ctx = MigrationContext.configure(engine)

    original_ctx = getattr(op, "_proxy", None)
    op._proxy = Operations(ctx)

    try:
        # 1. Run 001 upgrade
        mig_001.upgrade()

        pg_enums = mig_001.PG_ENUMS
        for enum_name in pg_enums:
            # Must have DO $$ block with IF NOT EXISTS check
            matching_do_blocks = [
                s for s in recorded_statements
                if f"IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}')" in s
            ]
            assert len(matching_do_blocks) == 1, f"Missing or duplicate DO block for enum {enum_name}"

            # Must NOT have raw CREATE TYPE {enum_name} emitted outside the DO block
            raw_creates = [
                s for s in recorded_statements
                if s.startswith(f"CREATE TYPE {enum_name}") or s.startswith(f"CREATE TYPE \"{enum_name}\"")
            ]
            assert len(raw_creates) == 0, f"Duplicate un-guarded CREATE TYPE emitted for {enum_name}: {raw_creates}"

        # 2. Run 002 upgrade
        mig_002.upgrade()

        outbox_do = [
            s for s in recorded_statements
            if "IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'outbox_status')" in s
        ]
        assert len(outbox_do) == 1, "Missing DO block for outbox_status"

        raw_outbox_creates = [
            s for s in recorded_statements
            if s.startswith("CREATE TYPE outbox_status") or s.startswith("CREATE TYPE \"outbox_status\"")
        ]
        assert len(raw_outbox_creates) == 0, f"Duplicate CREATE TYPE for outbox_status: {raw_outbox_creates}"

        # 3. Test downgrade sequence
        downgrade_statements = []
        def mock_down_executor(sql, *args, **kwargs):
            if hasattr(sql, "compile"):
                downgrade_statements.append(str(sql.compile(dialect=postgresql.dialect())).strip())
            else:
                downgrade_statements.append(str(sql).strip())

        engine_down = sa.create_mock_engine("postgresql://", mock_down_executor)
        op._proxy = Operations(MigrationContext.configure(engine_down))

        mig_002.downgrade()
        assert any("DROP TYPE IF EXISTS outbox_status CASCADE" in s for s in downgrade_statements)

        mig_001.downgrade()
        for enum_name in pg_enums:
            assert any(f"DROP TYPE IF EXISTS {enum_name} CASCADE" in s for s in downgrade_statements), (
                f"Missing DROP TYPE for {enum_name} in downgrade"
            )

    finally:
        op._proxy = original_ctx

