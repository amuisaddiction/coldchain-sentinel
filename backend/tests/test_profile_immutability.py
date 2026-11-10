"""Tests for ProductProfile and Shipment snapshot immutability, ORM listener protection, and bulk SQL documentation."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, event, update
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
    ImmutableProfileError,
    ImmutableSnapshotError,
)


@pytest.fixture
def db_session():
    """In-memory SQLite database session."""
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
def locked_profile_and_shipment(db_session):
    """Seed an organization, a locked profile, and an associated shipment."""
    org = Organization(name="Immutability Labs", slug="immutability-labs", status=OrganizationStatus.ACTIVE)
    db_session.add(org)
    db_session.commit()

    user = User(
        organization_id=org.id,
        email="auditor@immutability.com",
        hashed_password="pw",
        full_name="Lead Auditor",
        role=UserRole.AUDITOR,
    )
    profile = ProductProfile(
        organization_id=org.id,
        name="Insulin-ColdStandard",
        version=1,
        min_temperature_celsius=Decimal("2.00"),
        max_temperature_celsius=Decimal("8.00"),
        max_excursion_duration_seconds=600,
        expected_sampling_interval_seconds=300,
        max_sampling_gap_seconds=600,
        is_locked=True,
    )
    db_session.add_all([user, profile])
    db_session.commit()

    shipment = Shipment(
        organization_id=org.id,
        product_profile_id=profile.id,
        created_by=user.id,
        tracking_number="SHP-IMMUT-001",
        status=ShipmentStatus.IN_TRANSIT,
        origin="Copenhagen Hub",
        destination="Oslo Central Hospital",
        rule_profile_version=profile.version,
        rule_min_temperature_celsius=profile.min_temperature_celsius,
        rule_max_temperature_celsius=profile.max_temperature_celsius,
        rule_max_excursion_duration_seconds=profile.max_excursion_duration_seconds,
        rule_expected_sampling_interval_seconds=profile.expected_sampling_interval_seconds,
        rule_max_sampling_gap_seconds=profile.max_sampling_gap_seconds,
        rule_source_reference=f"{profile.name}:v1",
        rule_snapshot_json={"min": "2.00", "max": "8.00", "excursion_max": 600},
    )
    db_session.add(shipment)
    db_session.commit()

    return {"org": org, "user": user, "profile": profile, "shipment": shipment}


def test_locked_product_profile_orm_mutation_blocked(db_session, locked_profile_and_shipment):
    """Attempting in-place ORM mutation of temperature limits on a locked profile must raise ImmutableProfileError."""
    profile = locked_profile_and_shipment["profile"]
    assert profile.is_locked is True

    # Mutating min_temperature_celsius
    profile.min_temperature_celsius = Decimal("0.00")
    with pytest.raises(ImmutableProfileError, match="Cannot update 'min_temperature_celsius' on locked ProductProfile"):
        db_session.commit()
    db_session.rollback()

    # Mutating max_temperature_celsius
    profile = db_session.query(ProductProfile).filter_by(id=profile.id).one()
    profile.max_temperature_celsius = Decimal("10.00")
    with pytest.raises(ImmutableProfileError, match="Cannot update 'max_temperature_celsius' on locked ProductProfile"):
        db_session.commit()
    db_session.rollback()

    # Mutating excursion seconds
    profile = db_session.query(ProductProfile).filter_by(id=profile.id).one()
    profile.max_excursion_duration_seconds = 1200
    with pytest.raises(ImmutableProfileError, match="Cannot update 'max_excursion_duration_seconds' on locked ProductProfile"):
        db_session.commit()
    db_session.rollback()

    # Non-rule fields like is_active can still be toggled
    profile = db_session.query(ProductProfile).filter_by(id=profile.id).one()
    profile.is_active = False
    db_session.commit()
    assert profile.is_active is False


def test_unlocked_product_profile_orm_mutation_permitted(db_session, locked_profile_and_shipment):
    """Profiles that are not locked can be edited in place normally prior to consignment linkage."""
    org = locked_profile_and_shipment["org"]
    draft_profile = ProductProfile(
        organization_id=org.id,
        name="Draft Spec",
        version=1,
        min_temperature_celsius=Decimal("15.00"),
        max_temperature_celsius=Decimal("25.00"),
        is_locked=False,
    )
    db_session.add(draft_profile)
    db_session.commit()

    # Editing unlocked profile succeeds
    draft_profile.min_temperature_celsius = Decimal("16.00")
    db_session.commit()
    assert draft_profile.min_temperature_celsius == Decimal("16.00")


def test_shipment_rule_snapshot_orm_mutation_blocked(db_session, locked_profile_and_shipment):
    """Attempting in-place ORM mutation of a shipment's rule snapshot attributes must raise ImmutableSnapshotError."""
    shipment = locked_profile_and_shipment["shipment"]

    # Attempting to mutate rule_min_temperature_celsius
    shipment.rule_min_temperature_celsius = Decimal("-5.00")
    with pytest.raises(ImmutableSnapshotError, match="Cannot modify immutable rule snapshot field 'rule_min_temperature_celsius'"):
        db_session.commit()
    db_session.rollback()

    # Attempting to mutate rule_snapshot_json
    shipment = db_session.query(Shipment).filter_by(id=shipment.id).one()
    shipment.rule_snapshot_json = {"tampered": True}
    with pytest.raises(ImmutableSnapshotError, match="Cannot modify immutable rule snapshot field 'rule_snapshot_json'"):
        db_session.commit()
    db_session.rollback()

    # Operational status transitions are permitted
    shipment = db_session.query(Shipment).filter_by(id=shipment.id).one()
    shipment.status = ShipmentStatus.DELIVERED
    shipment.delivered_at = datetime.now(timezone.utc)
    db_session.commit()
    assert shipment.status == ShipmentStatus.DELIVERED


def test_bulk_sql_bypass_demonstration_and_documentation(db_session, locked_profile_and_shipment):
    """
    Demonstrates and documents that direct raw SQL / bulk update statements bypass Python ORM instance listeners.
    This test verifies that Python ORM listeners are application-layer controls, not database-level triggers.
    """
    profile = locked_profile_and_shipment["profile"]
    assert profile.is_locked is True

    # Bulk SQL update statement (bypasses ORM instance-level before_update listeners)
    stmt = (
        update(ProductProfile)
        .where(ProductProfile.id == profile.id)
        .values(min_temperature_celsius=Decimal("-10.00"))
    )
    db_session.execute(stmt)
    db_session.commit()

    # Reload from database to verify bulk SQL bypassed the ORM hook
    db_session.expire_all()
    updated_profile = db_session.query(ProductProfile).filter_by(id=profile.id).one()
    assert updated_profile.min_temperature_celsius == Decimal("-10.00")

    # Critical Assertion: The shipment's independent snapshot remains pristine and unchanged
    shipment = db_session.query(Shipment).filter_by(id=locked_profile_and_shipment["shipment"].id).one()
    assert shipment.rule_min_temperature_celsius == Decimal("2.00")
    assert shipment.rule_snapshot_json["min"] == "2.00"


def test_profile_versioning_isolation(db_session, locked_profile_and_shipment):
    """
    Creating a new profile version (v2) leaves existing shipments referencing v1 completely unaffected.
    """
    data = locked_profile_and_shipment
    org = data["org"]
    user = data["user"]
    shp_v1 = data["shipment"]

    # Create Version 2 of profile with tighter requirements (1.00 to 5.00)
    profile_v2 = ProductProfile(
        organization_id=org.id,
        name="Insulin-ColdStandard",
        version=2,
        min_temperature_celsius=Decimal("1.00"),
        max_temperature_celsius=Decimal("5.00"),
        max_excursion_duration_seconds=300,
        expected_sampling_interval_seconds=120,
        max_sampling_gap_seconds=300,
        is_locked=True,
    )
    db_session.add(profile_v2)
    db_session.commit()

    # Create Shipment 2 referencing Profile v2
    shp_v2 = Shipment(
        organization_id=org.id,
        product_profile_id=profile_v2.id,
        created_by=user.id,
        tracking_number="SHP-IMMUT-002",
        status=ShipmentStatus.CREATED,
        origin="Copenhagen Hub",
        destination="Stockholm Clinic",
        rule_profile_version=profile_v2.version,
        rule_min_temperature_celsius=profile_v2.min_temperature_celsius,
        rule_max_temperature_celsius=profile_v2.max_temperature_celsius,
        rule_max_excursion_duration_seconds=profile_v2.max_excursion_duration_seconds,
        rule_expected_sampling_interval_seconds=profile_v2.expected_sampling_interval_seconds,
        rule_max_sampling_gap_seconds=profile_v2.max_sampling_gap_seconds,
        rule_source_reference=f"{profile_v2.name}:v2",
        rule_snapshot_json={"min": "1.00", "max": "5.00", "excursion_max": 300},
    )
    db_session.add(shp_v2)
    db_session.commit()

    # Assert Shipment 1 rules are strictly isolated to v1 values
    db_session.refresh(shp_v1)
    db_session.refresh(shp_v2)

    assert shp_v1.rule_profile_version == 1
    assert shp_v1.rule_min_temperature_celsius == Decimal("2.00")
    assert shp_v1.rule_max_temperature_celsius == Decimal("8.00")
    assert shp_v1.rule_snapshot_json["min"] == "2.00"

    assert shp_v2.rule_profile_version == 2
    assert shp_v2.rule_min_temperature_celsius == Decimal("1.00")
    assert shp_v2.rule_max_temperature_celsius == Decimal("5.00")
    assert shp_v2.rule_snapshot_json["min"] == "1.00"
