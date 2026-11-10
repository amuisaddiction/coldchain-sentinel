"""Unit tests for all 12 SQLAlchemy models, data types, and database CHECK constraints."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    Organization,
    OrganizationStatus,
    User,
    UserRole,
    ProductProfile,
    Shipment,
    ShipmentStatus,
    EvidenceFile,
    EvidenceType,
    EvidenceIntegrityStatus,
    TemperatureReading,
    TemperatureSeverity,
    CustodyEvent,
    CustodyEventType,
    VerificationDecision,
    DecisionType,
    Payment,
    PaymentStatus,
    PaymentAction,
    PaymentIdempotencyRecord,
    IdempotencyStatus,
    Investigation,
    InvestigationStatus,
    InvestigationPriority,
    AuditEvent,
)


@pytest.fixture
def db_session():
    """In-memory SQLite database session with enforced foreign keys."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_model_instantiation_and_persistence(db_session):
    """Verify all 12 models can be persisted, relationships navigated, and retrieved with accurate types."""
    # 1. Organization
    org = Organization(
        name="PharmaCore Global",
        slug="pharmacore-global",
        status=OrganizationStatus.ACTIVE,
    )
    db_session.add(org)
    db_session.commit()
    assert org.id is not None
    assert org.created_at.tzinfo == timezone.utc

    # 2. User
    user = User(
        organization_id=org.id,
        email="qa.lead@pharmacore.com",
        hashed_password="secure_argon2_hash",
        full_name="Dr. Jane Smith",
        role=UserRole.QUALITY_ASSURANCE,
    )
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
    assert user.organization.name == "PharmaCore Global"

    # 3. ProductProfile
    profile = ProductProfile(
        organization_id=org.id,
        name="mRNA-BioFreeze-Standard",
        version=1,
        min_temperature_celsius=Decimal("-80.00"),
        max_temperature_celsius=Decimal("-60.00"),
        max_excursion_duration_seconds=300,
        expected_sampling_interval_seconds=60,
        max_sampling_gap_seconds=180,
    )
    db_session.add(profile)
    db_session.commit()
    assert isinstance(profile.min_temperature_celsius, Decimal)
    assert profile.min_temperature_celsius == Decimal("-80.00")

    # 4. Shipment
    shipment = Shipment(
        organization_id=org.id,
        product_profile_id=profile.id,
        created_by=user.id,
        tracking_number="SHP-2026-001-XYZ",
        status=ShipmentStatus.CREATED,
        origin="Main Warehouse, Basel",
        destination="General Hospital, Geneva",
        rule_profile_version=profile.version,
        rule_min_temperature_celsius=profile.min_temperature_celsius,
        rule_max_temperature_celsius=profile.max_temperature_celsius,
        rule_max_excursion_duration_seconds=profile.max_excursion_duration_seconds,
        rule_expected_sampling_interval_seconds=profile.expected_sampling_interval_seconds,
        rule_max_sampling_gap_seconds=profile.max_sampling_gap_seconds,
        rule_source_reference=f"{profile.name}:v{profile.version}",
        rule_snapshot_json={"min": "-80.00", "max": "-60.00", "unit": "CELSIUS"},
    )
    db_session.add(shipment)
    db_session.commit()
    assert shipment.id is not None
    assert isinstance(shipment.rule_min_temperature_celsius, Decimal)

    # 5. EvidenceFile
    evidence = EvidenceFile(
        shipment_id=shipment.id,
        organization_id=org.id,
        file_type=EvidenceType.LOGGER_CSV,
        original_filename="logger_sn9942.csv",
        storage_path="evidence/2026/logger_sn9942.csv",
        file_size_bytes=45200,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        integrity_status=EvidenceIntegrityStatus.VERIFIED,
        uploaded_by=user.id,
        parsed_records_count=500,
    )
    db_session.add(evidence)
    db_session.commit()
    assert evidence.id is not None

    # 6. TemperatureReading
    reading = TemperatureReading(
        shipment_id=shipment.id,
        evidence_file_id=evidence.id,
        row_number=1,
        sensor_id="PROBE-01",
        recorded_at=datetime.now(timezone.utc),
        temperature_celsius=Decimal("-72.40"),
        severity=TemperatureSeverity.NORMAL,
        sequence_number=1,
    )
    db_session.add(reading)
    db_session.commit()
    assert reading.id is not None
    assert isinstance(reading.temperature_celsius, Decimal)
    assert reading.temperature_celsius == Decimal("-72.40")

    # 7. CustodyEvent
    custody = CustodyEvent(
        shipment_id=shipment.id,
        organization_id=org.id,
        evidence_file_id=evidence.id,
        actor_user_id=user.id,
        event_type=CustodyEventType.DISPATCH,
        carrier_name="ColdFleet Logistics",
        custodian_name="Mark Driver",
        location="Basel Hub",
        notes="Pre-cooled container verified",
        recorded_at=datetime.now(timezone.utc),
    )
    db_session.add(custody)
    db_session.commit()
    assert custody.id is not None

    # 8. VerificationDecision
    decision = VerificationDecision(
        shipment_id=shipment.id,
        organization_id=org.id,
        decision=DecisionType.PASSED,
        confidence_score=Decimal("0.995"),
        evidence_hash_snapshot=evidence.sha256_hash,
        temperature_rule_passed=True,
        custody_chain_passed=True,
        sampling_frequency_passed=True,
        total_excursion_seconds=0,
        max_temperature_detected=Decimal("-70.20"),
        min_temperature_detected=Decimal("-74.50"),
        reasoning_summary="All 500 readings compliant within -80 to -60 range.",
        decided_by=user.id,
    )
    db_session.add(decision)
    db_session.commit()
    assert decision.id is not None
    assert decision.confidence_score == Decimal("0.995")

    # 9. Payment
    payment = Payment(
        shipment_id=shipment.id,
        organization_id=org.id,
        payment_provider="PAYPAL",
        paypal_order_id="ORD-99882233",
        paypal_authorization_id="AUTH-77665544",
        amount_minor=150000,
        currency="USD",
        currency_exponent=2,
        status=PaymentStatus.AUTHORIZED,
    )
    db_session.add(payment)
    db_session.commit()
    assert payment.id is not None
    assert payment.amount_minor == 150000

    # 10. PaymentIdempotencyRecord
    idempotency = PaymentIdempotencyRecord(
        provider="PAYPAL",
        action=PaymentAction.CAPTURE,
        idempotency_key="idemp_cap_shp_2026_001",
        organization_id=org.id,
        payment_id=payment.id,
        status=IdempotencyStatus.IN_PROGRESS,
        request_hash="a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add(idempotency)
    db_session.commit()
    assert idempotency.id is not None

    # 11. Investigation
    investigation = Investigation(
        shipment_id=shipment.id,
        organization_id=org.id,
        assigned_to=user.id,
        status=InvestigationStatus.OPEN,
        priority=InvestigationPriority.LOW,
        findings="Routine check.",
    )
    db_session.add(investigation)
    db_session.commit()
    assert investigation.id is not None

    # 12. AuditEvent
    audit = AuditEvent(
        organization_id=org.id,
        user_id=user.id,
        shipment_id=shipment.id,
        entity_type="shipments",
        entity_id=shipment.id,
        action="SHIPMENT_CREATED",
        payload_after={"tracking_number": shipment.tracking_number},
    )
    db_session.add(audit)
    db_session.commit()
    assert audit.id is not None


def test_product_profile_check_constraints(db_session):
    """Verify CHECK constraints on ProductProfile limits and sampling intervals."""
    org = Organization(name="Org Checks", slug="org-checks")
    db_session.add(org)
    db_session.commit()

    # min_temp >= max_temp
    p_invalid_temp = ProductProfile(
        organization_id=org.id,
        name="Bad-Temp",
        version=1,
        min_temperature_celsius=Decimal("10.00"),
        max_temperature_celsius=Decimal("5.00"),
    )
    db_session.add(p_invalid_temp)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # sampling_interval <= 0
    p_invalid_interval = ProductProfile(
        organization_id=org.id,
        name="Bad-Interval",
        version=1,
        min_temperature_celsius=Decimal("2.00"),
        max_temperature_celsius=Decimal("8.00"),
        expected_sampling_interval_seconds=0,
    )
    db_session.add(p_invalid_interval)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # max_gap < expected_interval
    p_invalid_gap = ProductProfile(
        organization_id=org.id,
        name="Bad-Gap",
        version=1,
        min_temperature_celsius=Decimal("2.00"),
        max_temperature_celsius=Decimal("8.00"),
        expected_sampling_interval_seconds=300,
        max_sampling_gap_seconds=200,
    )
    db_session.add(p_invalid_gap)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_payment_and_decision_check_constraints(db_session):
    """Verify CHECK constraints on Payment monetary amounts and Decision confidence scores."""
    org = Organization(name="Fin Org", slug="fin-org")
    db_session.add(org)
    db_session.commit()

    profile = ProductProfile(
        organization_id=org.id,
        name="Standard P",
        version=1,
        min_temperature_celsius=Decimal("2.00"),
        max_temperature_celsius=Decimal("8.00"),
    )
    db_session.add(profile)
    db_session.commit()

    shipment = Shipment(
        organization_id=org.id,
        product_profile_id=profile.id,
        tracking_number="FIN-TEST-001",
        origin="A",
        destination="B",
        rule_profile_version=1,
        rule_min_temperature_celsius=Decimal("2.00"),
        rule_max_temperature_celsius=Decimal("8.00"),
        rule_max_excursion_duration_seconds=0,
        rule_expected_sampling_interval_seconds=60,
        rule_max_sampling_gap_seconds=120,
        rule_source_reference="Ref",
        rule_snapshot_json={},
    )
    db_session.add(shipment)
    db_session.commit()

    # Payment amount_minor <= 0
    bad_payment = Payment(
        shipment_id=shipment.id,
        organization_id=org.id,
        payment_provider="PAYPAL",
        amount_minor=0,
        currency="USD",
        currency_exponent=2,
    )
    db_session.add(bad_payment)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Payment invalid currency exponent
    bad_exp_payment = Payment(
        shipment_id=shipment.id,
        organization_id=org.id,
        payment_provider="PAYPAL",
        amount_minor=1000,
        currency="USD",
        currency_exponent=5,
    )
    db_session.add(bad_exp_payment)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Decision confidence_score > 1.000
    bad_decision = VerificationDecision(
        shipment_id=shipment.id,
        organization_id=org.id,
        decision=DecisionType.PASSED,
        confidence_score=Decimal("1.500"),
        evidence_hash_snapshot="dummy_hash",
        temperature_rule_passed=True,
        custody_chain_passed=True,
        sampling_frequency_passed=True,
        total_excursion_seconds=0,
        reasoning_summary="Too confident",
    )
    db_session.add(bad_decision)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
