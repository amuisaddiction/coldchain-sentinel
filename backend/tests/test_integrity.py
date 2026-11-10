"""Tests for multi-tenant isolation, composite foreign keys, deletion policies, and integrity constraints."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
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
    """Isolated in-memory SQLite database session with enforced foreign keys."""
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


@pytest.fixture
def seed_orgs_and_users(db_session):
    """Fixture providing two distinct organizations with users and product profiles."""
    # Org A
    org_a = Organization(name="Pharma Corp A", slug="pharma-a", status=OrganizationStatus.ACTIVE)
    db_session.add(org_a)
    db_session.commit()

    user_a = User(
        organization_id=org_a.id,
        email="operator@pharma-a.com",
        hashed_password="pw",
        full_name="Alice A",
        role=UserRole.OPERATOR,
    )
    profile_a = ProductProfile(
        organization_id=org_a.id,
        name="Vaccine A",
        version=1,
        min_temperature_celsius=Decimal("2.00"),
        max_temperature_celsius=Decimal("8.00"),
    )
    db_session.add_all([user_a, profile_a])
    db_session.commit()

    # Org B
    org_b = Organization(name="Pharma Corp B", slug="pharma-b", status=OrganizationStatus.ACTIVE)
    db_session.add(org_b)
    db_session.commit()

    user_b = User(
        organization_id=org_b.id,
        email="operator@pharma-b.com",
        hashed_password="pw",
        full_name="Bob B",
        role=UserRole.OPERATOR,
    )
    profile_b = ProductProfile(
        organization_id=org_b.id,
        name="Insulin B",
        version=1,
        min_temperature_celsius=Decimal("15.00"),
        max_temperature_celsius=Decimal("25.00"),
    )
    db_session.add_all([user_b, profile_b])
    db_session.commit()

    return {
        "org_a": org_a,
        "user_a": user_a,
        "profile_a": profile_a,
        "org_b": org_b,
        "user_b": user_b,
        "profile_b": profile_b,
    }


def test_cross_org_product_profile_rejection(db_session, seed_orgs_and_users):
    """Attempting to create a shipment in Org A using Org B's product profile must fail composite FK."""
    d = seed_orgs_and_users
    # Org A shipment referencing Org B profile
    shipment = Shipment(
        organization_id=d["org_a"].id,
        product_profile_id=d["profile_b"].id,  # Cross-tenant violation!
        created_by=d["user_a"].id,
        tracking_number="SHP-CROSS-001",
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
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cross_org_creator_rejection(db_session, seed_orgs_and_users):
    """Attempting to create a shipment in Org A using Org B's user must fail composite FK."""
    d = seed_orgs_and_users
    shipment = Shipment(
        organization_id=d["org_a"].id,
        product_profile_id=d["profile_a"].id,
        created_by=d["user_b"].id,  # Cross-tenant violation!
        tracking_number="SHP-CROSS-002",
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
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_nullable_actors_permissibility(db_session, seed_orgs_and_users):
    """Nullable actor IDs (e.g. system automation, unassigned) must insert cleanly when NULL."""
    d = seed_orgs_and_users

    # 1. Shipment created by automation (created_by=None)
    shipment = Shipment(
        organization_id=d["org_a"].id,
        product_profile_id=d["profile_a"].id,
        created_by=None,
        tracking_number="SHP-AUTO-001",
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
    assert shipment.created_by is None

    # 2. Custody event with no internal user (actor_user_id=None)
    custody = CustodyEvent(
        shipment_id=shipment.id,
        organization_id=d["org_a"].id,
        actor_user_id=None,
        event_type=CustodyEventType.AIRPORT_TRANSFER,
        carrier_name="AirCargo Lux",
        custodian_name="External Agent",
        location="Frankfurt Airport",
        recorded_at=datetime.now(timezone.utc),
    )
    db_session.add(custody)
    db_session.commit()
    assert custody.actor_user_id is None

    # 3. Decision with automated engine (decided_by=None)
    decision = VerificationDecision(
        shipment_id=shipment.id,
        organization_id=d["org_a"].id,
        decision=DecisionType.PASSED,
        confidence_score=Decimal("1.000"),
        evidence_hash_snapshot="hash_abc",
        temperature_rule_passed=True,
        custody_chain_passed=True,
        sampling_frequency_passed=True,
        total_excursion_seconds=0,
        reasoning_summary="Pure engine verification",
        decided_by=None,
    )
    db_session.add(decision)
    db_session.commit()
    assert decision.decided_by is None

    # 4. Investigation unassigned (assigned_to=None)
    investigation = Investigation(
        shipment_id=shipment.id,
        organization_id=d["org_a"].id,
        assigned_to=None,
        status=InvestigationStatus.OPEN,
        priority=InvestigationPriority.HIGH,
    )
    db_session.add(investigation)
    db_session.commit()
    assert investigation.assigned_to is None

    # 5. Audit event system task (user_id=None, shipment_id=None)
    audit = AuditEvent(
        organization_id=d["org_a"].id,
        user_id=None,
        shipment_id=None,
        entity_type="system",
        entity_id="cron-001",
        action="BATCH_CLEANUP",
    )
    db_session.add(audit)
    db_session.commit()
    assert audit.user_id is None


def test_cross_org_actor_rejections(db_session, seed_orgs_and_users):
    """When actor IDs are provided, they must match the consignment's organization."""
    d = seed_orgs_and_users
    shipment = Shipment(
        organization_id=d["org_a"].id,
        product_profile_id=d["profile_a"].id,
        created_by=d["user_a"].id,
        tracking_number="SHP-ACTOR-001",
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

    # Evidence uploaded by Org B user in Org A shipment
    bad_evidence = EvidenceFile(
        shipment_id=shipment.id,
        organization_id=d["org_a"].id,
        file_type=EvidenceType.LOGGER_CSV,
        original_filename="test.csv",
        storage_path="path",
        file_size_bytes=100,
        sha256_hash="hash1",
        uploaded_by=d["user_b"].id,  # Cross-tenant!
    )
    db_session.add(bad_evidence)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Custody event with Org B actor in Org A shipment
    bad_custody = CustodyEvent(
        shipment_id=shipment.id,
        organization_id=d["org_a"].id,
        actor_user_id=d["user_b"].id,  # Cross-tenant!
        event_type=CustodyEventType.DISPATCH,
        carrier_name="Carrier",
        custodian_name="Custodian",
        location="Loc",
        recorded_at=datetime.now(timezone.utc),
    )
    db_session.add(bad_custody)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Investigation assigned to Org B user in Org A shipment
    bad_inv = Investigation(
        shipment_id=shipment.id,
        organization_id=d["org_a"].id,
        assigned_to=d["user_b"].id,  # Cross-tenant!
        status=InvestigationStatus.OPEN,
        priority=InvestigationPriority.MEDIUM,
    )
    db_session.add(bad_inv)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_custody_evidence_deletion_restriction(db_session, seed_orgs_and_users):
    """Deleting an evidence file referenced by a custody handover event must be blocked (ON DELETE RESTRICT)."""
    d = seed_orgs_and_users
    shipment = Shipment(
        organization_id=d["org_a"].id,
        product_profile_id=d["profile_a"].id,
        created_by=d["user_a"].id,
        tracking_number="SHP-DEL-001",
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

    evidence = EvidenceFile(
        shipment_id=shipment.id,
        organization_id=d["org_a"].id,
        file_type=EvidenceType.DELIVERY_MANIFEST,
        original_filename="manifest.pdf",
        storage_path="path/manifest.pdf",
        file_size_bytes=5000,
        sha256_hash="manifest_hash_123",
        uploaded_by=d["user_a"].id,
    )
    db_session.add(evidence)
    db_session.commit()

    custody = CustodyEvent(
        shipment_id=shipment.id,
        organization_id=d["org_a"].id,
        evidence_file_id=evidence.id,
        actor_user_id=d["user_a"].id,
        event_type=CustodyEventType.DELIVERY_HANDOVER,
        carrier_name="DHL Health",
        custodian_name="Hospital Pharmacist",
        location="Geneva Clinic",
        recorded_at=datetime.now(timezone.utc),
    )
    db_session.add(custody)
    db_session.commit()

    # Attempting to delete evidence file while linked to custody event must raise IntegrityError
    db_session.delete(evidence)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Service-level safe unlink: set custody.evidence_file_id = None, then delete
    custody_rec = db_session.query(CustodyEvent).filter_by(id=custody.id).one()
    custody_rec.evidence_file_id = None
    db_session.commit()

    ev_rec = db_session.query(EvidenceFile).filter_by(id=evidence.id).one()
    db_session.delete(ev_rec)
    db_session.commit()
    assert db_session.query(EvidenceFile).filter_by(id=evidence.id).first() is None


def test_temperature_readings_multi_sensor_concurrency(db_session, seed_orgs_and_users):
    """Verify that multiple sensors can record at the same timestamp, while duplicate rows are blocked."""
    d = seed_orgs_and_users
    shipment = Shipment(
        organization_id=d["org_a"].id,
        product_profile_id=d["profile_a"].id,
        created_by=d["user_a"].id,
        tracking_number="SHP-SENSORS-001",
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

    evidence = EvidenceFile(
        shipment_id=shipment.id,
        organization_id=d["org_a"].id,
        file_type=EvidenceType.LOGGER_CSV,
        original_filename="multi.csv",
        storage_path="path/multi.csv",
        file_size_bytes=2000,
        sha256_hash="multi_hash_123",
        uploaded_by=d["user_a"].id,
    )
    db_session.add(evidence)
    db_session.commit()

    now = datetime.now(timezone.utc)

    # Sensor 1 at timestamp 'now'
    r1 = TemperatureReading(
        shipment_id=shipment.id,
        evidence_file_id=evidence.id,
        row_number=1,
        sensor_id="PROBE-TOP",
        recorded_at=now,
        temperature_celsius=Decimal("4.50"),
    )
    # Sensor 2 at exact same timestamp 'now' -> must succeed!
    r2 = TemperatureReading(
        shipment_id=shipment.id,
        evidence_file_id=evidence.id,
        row_number=2,
        sensor_id="PROBE-BOTTOM",
        recorded_at=now,
        temperature_celsius=Decimal("4.80"),
    )
    db_session.add_all([r1, r2])
    db_session.commit()
    assert r1.id is not None
    assert r2.id is not None

    # Ingesting duplicate row_number for same evidence_file_id must fail unique constraint
    duplicate_row = TemperatureReading(
        shipment_id=shipment.id,
        evidence_file_id=evidence.id,
        row_number=1,  # Duplicate row 1!
        sensor_id="PROBE-TOP",
        recorded_at=datetime.now(timezone.utc),
        temperature_celsius=Decimal("4.50"),
    )
    db_session.add(duplicate_row)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_payment_idempotency_and_deletion_restriction(db_session, seed_orgs_and_users):
    """Verify unique idempotency keys, payment retention (ON DELETE RESTRICT), and recovery state transitions."""
    d = seed_orgs_and_users
    shipment = Shipment(
        organization_id=d["org_a"].id,
        product_profile_id=d["profile_a"].id,
        tracking_number="SHP-PAY-IDEMP-001",
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

    payment = Payment(
        shipment_id=shipment.id,
        organization_id=d["org_a"].id,
        payment_provider="PAYPAL",
        paypal_order_id="ORD-111",
        paypal_authorization_id="AUTH-111",
        amount_minor=50000,
        currency="USD",
        currency_exponent=2,
    )
    db_session.add(payment)
    db_session.commit()

    idemp1 = PaymentIdempotencyRecord(
        provider="PAYPAL",
        action=PaymentAction.CAPTURE,
        idempotency_key="idemp_key_unique_123",
        organization_id=d["org_a"].id,
        payment_id=payment.id,
        status=IdempotencyStatus.IN_PROGRESS,
        request_hash="hash_req_1",
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add(idemp1)
    db_session.commit()

    # Re-inserting same (provider, action, idempotency_key) must violate unique constraint
    idemp2 = PaymentIdempotencyRecord(
        provider="PAYPAL",
        action=PaymentAction.CAPTURE,
        idempotency_key="idemp_key_unique_123",
        organization_id=d["org_a"].id,
        payment_id=payment.id,
        status=IdempotencyStatus.IN_PROGRESS,
        request_hash="hash_req_2",
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add(idemp2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Attempting to delete payment while idempotency record references it must fail (ON DELETE RESTRICT)
    pay_rec = db_session.query(Payment).filter_by(id=payment.id).one()
    db_session.delete(pay_rec)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Verify recovery state transition
    idemp_rec = db_session.query(PaymentIdempotencyRecord).filter_by(idempotency_key="idemp_key_unique_123").one()
    assert idemp_rec.status == IdempotencyStatus.IN_PROGRESS
    idemp_rec.status = IdempotencyStatus.REQUIRES_RECONCILIATION
    db_session.commit()
    assert idemp_rec.status == IdempotencyStatus.REQUIRES_RECONCILIATION
