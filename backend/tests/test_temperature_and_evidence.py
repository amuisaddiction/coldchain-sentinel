"""Tests for Phase 6 & 7: Temperature Intelligence, Evidence Trust Engine, and Tamper Detection."""

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.enums import (
    ShipmentStatus,
    EvidenceType,
    EvidenceIntegrityStatus,
    DecisionType,
    TemperatureSeverity,
)
from app.services import (
    organization_service,
    product_profile_service,
    shipment_service,
    evidence_service,
    temperature_service,
)


@pytest.fixture
def evidence_env(tmp_path):
    """Setup isolated test database and temporary storage."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    # Override storage path to temp dir
    from app.core.config import settings
    settings.STORAGE_LOCAL_PATH = str(tmp_path / "storage")

    org, admin = organization_service.create_organization(
        db=db,
        name="ThermoShield Logistics",
        slug="thermoshield",
        admin_email="admin@thermoshield.com",
        admin_password="Password123!",
        admin_name="Thermo Admin",
    )

    # 2°C to 8°C cold chain profile with 600s allowed excursion
    profile = product_profile_service.create_profile(
        db=db,
        org_id=org.id,
        name="Standard Vaccine 2-8C",
        min_temp=Decimal("2.00"),
        max_temp=Decimal("8.00"),
        max_excursion_seconds=600,
        expected_sampling_seconds=300,
        max_gap_seconds=900,
        user_id=admin.id,
    )

    shipment = shipment_service.create_shipment(
        db=db,
        org_id=org.id,
        product_profile_id=profile.id,
        tracking_number="TS-2026-TEST",
        origin="Zurich Distribution Hub",
        destination="Geneva University Hospital",
        created_by_user_id=admin.id,
    )

    # Move shipment to DELIVERED so it can be verified
    shipment_service.update_shipment_status(db=db, org_id=org.id, shipment_id=shipment.id, new_status=ShipmentStatus.IN_TRANSIT)
    shipment_service.update_shipment_status(db=db, org_id=org.id, shipment_id=shipment.id, new_status=ShipmentStatus.DELIVERED)

    yield {
        "db": db,
        "org": org,
        "admin": admin,
        "profile": profile,
        "shipment": shipment,
    }
    db.close()


def test_evidence_upload_and_tamper_detection(evidence_env):
    """Verify evidence file upload, SHA-256 recording, and cryptographic tamper detection."""
    db = evidence_env["db"]
    org = evidence_env["org"]
    admin = evidence_env["admin"]
    shipment = evidence_env["shipment"]

    # 1. Upload logger CSV
    csv_content = (
        b"timestamp,temperature,sensor_id\n"
        b"2026-11-01T10:00:00Z,4.5,LOGGER-01\n"
        b"2026-11-01T10:05:00Z,5.1,LOGGER-01\n"
        b"2026-11-01T10:10:00Z,4.8,LOGGER-01\n"
    )

    evidence = evidence_service.upload_evidence(
        db=db,
        org_id=org.id,
        shipment_id=shipment.id,
        file_type=EvidenceType.LOGGER_CSV,
        original_filename="logger_log.csv",
        content=csv_content,
        uploaded_by_user_id=admin.id,
    )

    assert evidence.id is not None
    assert evidence.sha256_hash is not None
    assert evidence.integrity_status == EvidenceIntegrityStatus.VERIFIED
    assert evidence.parsed_records_count == 3

    # 2. Verify clean integrity check
    check_clean = evidence_service.verify_evidence_integrity(
        db=db,
        org_id=org.id,
        evidence_id=evidence.id,
    )
    assert check_clean.is_tampered is False
    assert check_clean.integrity_status == EvidenceIntegrityStatus.VERIFIED

    # 3. Simulate unauthorized byte alteration in storage
    storage = evidence_service.get_storage()
    tampered_bytes = csv_content + b"\nTAMPERED_ROW,99.9,HACK"
    import os
    abs_path = os.path.join(storage.base_path, evidence.storage_path)
    with open(abs_path, "wb") as f:
        f.write(tampered_bytes)

    # 4. Re-verify integrity -> MUST detect tampering!
    check_tampered = evidence_service.verify_evidence_integrity(
        db=db,
        org_id=org.id,
        evidence_id=evidence.id,
    )
    assert check_tampered.is_tampered is True
    assert check_tampered.integrity_status == EvidenceIntegrityStatus.HASH_MISMATCH
    assert "TAMPER DETECTED" in check_tampered.message


def test_temperature_compliance_evaluation_pass(evidence_env):
    """Verify temperature evaluation calculates PASSED decision when readings are compliant."""
    db = evidence_env["db"]
    org = evidence_env["org"]
    admin = evidence_env["admin"]
    shipment = evidence_env["shipment"]

    # All readings within 2.00C - 8.00C range
    compliant_csv = (
        b"timestamp,temperature,sensor_id\n"
        b"2026-11-01T10:00:00Z,3.5,LOGGER-01\n"
        b"2026-11-01T10:05:00Z,4.2,LOGGER-01\n"
        b"2026-11-01T10:10:00Z,5.0,LOGGER-01\n"
        b"2026-11-01T10:15:00Z,4.8,LOGGER-01\n"
    )

    evidence_service.upload_evidence(
        db=db,
        org_id=org.id,
        shipment_id=shipment.id,
        file_type=EvidenceType.LOGGER_CSV,
        original_filename="compliant_run.csv",
        content=compliant_csv,
        uploaded_by_user_id=admin.id,
    )

    decision = temperature_service.evaluate_shipment_compliance(
        db=db,
        org_id=org.id,
        shipment_id=shipment.id,
        decided_by_user_id=admin.id,
    )

    assert decision.decision == DecisionType.PASSED
    assert decision.temperature_rule_passed is True
    assert decision.total_excursion_seconds == 0
    assert decision.confidence_score == Decimal("1.000")

    # Shipment status updated to VERIFIED
    db.refresh(shipment)
    assert shipment.status == ShipmentStatus.VERIFIED


def test_temperature_compliance_evaluation_fail_on_excursion(evidence_env):
    """Verify temperature evaluation calculates FAILED decision when excursion budget is exceeded."""
    db = evidence_env["db"]
    org = evidence_env["org"]
    admin = evidence_env["admin"]
    shipment = evidence_env["shipment"]

    # Excursion allowed budget is 600s. 3 intervals of 300s = 900s excursion!
    excursion_csv = (
        b"timestamp,temperature,sensor_id\n"
        b"2026-11-01T10:00:00Z,12.5,LOGGER-01\n"  # Excursion 1 (+300s)
        b"2026-11-01T10:05:00Z,13.0,LOGGER-01\n"  # Excursion 2 (+300s)
        b"2026-11-01T10:10:00Z,11.8,LOGGER-01\n"  # Excursion 3 (+300s = 900s > 600s budget)
        b"2026-11-01T10:15:00Z,4.5,LOGGER-01\n"
    )

    evidence_service.upload_evidence(
        db=db,
        org_id=org.id,
        shipment_id=shipment.id,
        file_type=EvidenceType.LOGGER_CSV,
        original_filename="excursion_run.csv",
        content=excursion_csv,
        uploaded_by_user_id=admin.id,
    )

    decision = temperature_service.evaluate_shipment_compliance(
        db=db,
        org_id=org.id,
        shipment_id=shipment.id,
        decided_by_user_id=admin.id,
    )

    assert decision.decision == DecisionType.FAILED
    assert decision.temperature_rule_passed is False
    assert decision.total_excursion_seconds == 900

    # Shipment status updated to FAILED
    db.refresh(shipment)
    assert shipment.status == ShipmentStatus.FAILED
