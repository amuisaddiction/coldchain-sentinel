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

    # Verify all 12 tables compiled to PostgreSQL syntax
    assert len(compiled_ddl) == 12

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
