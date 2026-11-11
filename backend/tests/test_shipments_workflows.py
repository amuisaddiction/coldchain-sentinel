"""Tests for Phase 5 Shipment creation, snapshot rules, lifecycle state machine, and tenant isolation."""

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.database import Base
from app.models.enums import ShipmentStatus, UserRole
from app.services import organization_service, user_service, product_profile_service, shipment_service


@pytest.fixture
def shipment_db():
    """Setup isolated in-memory SQLite database seeded with two organizations and product profiles."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    # Seed Org A
    org_a, admin_a = organization_service.create_organization(
        db=db,
        name="Pfizer Cold Logistics",
        slug="pfizer-logistics",
        admin_email="admin@pfizer-logistics.com",
        admin_password="Password123!",
        admin_name="Pfizer Admin",
    )
    profile_a = product_profile_service.create_profile(
        db=db,
        org_id=org_a.id,
        name="mRNA-1273 Deep Freeze",
        min_temp=Decimal("-25.00"),
        max_temp=Decimal("-15.00"),
        max_excursion_seconds=3600,
        expected_sampling_seconds=300,
        max_gap_seconds=600,
        user_id=admin_a.id,
    )

    # Seed Org B
    org_b, admin_b = organization_service.create_organization(
        db=db,
        name="Moderna Supply",
        slug="moderna-supply",
        admin_email="admin@moderna-supply.com",
        admin_password="Password123!",
        admin_name="Moderna Admin",
    )
    profile_b = product_profile_service.create_profile(
        db=db,
        org_id=org_b.id,
        name="Spikevax Standard",
        min_temp=Decimal("2.00"),
        max_temp=Decimal("8.00"),
        max_excursion_seconds=1800,
        expected_sampling_seconds=120,
        max_gap_seconds=300,
        user_id=admin_b.id,
    )

    yield {
        "db": db,
        "org_a": org_a,
        "admin_a": admin_a,
        "profile_a": profile_a,
        "org_b": org_b,
        "admin_b": admin_b,
        "profile_b": profile_b,
    }
    db.close()


def test_shipment_creation_and_snapshot_immutability(shipment_db):
    """Verify shipment creation captures an immutable snapshot of profile rules and locks the profile."""
    db = shipment_db["db"]
    org_a = shipment_db["org_a"]
    admin_a = shipment_db["admin_a"]
    profile_a = shipment_db["profile_a"]

    assert profile_a.is_locked is False

    shipment = shipment_service.create_shipment(
        db=db,
        org_id=org_a.id,
        product_profile_id=profile_a.id,
        tracking_number="PFIZ-2026-0001",
        origin="Kalamazoo, MI Facility",
        destination="Boston Medical Center",
        created_by_user_id=admin_a.id,
    )

    # Verify shipment fields
    assert shipment.id is not None
    assert shipment.status == ShipmentStatus.CREATED
    assert shipment.tracking_number == "PFIZ-2026-0001"
    assert shipment.rule_min_temperature_celsius == Decimal("-25.00")
    assert shipment.rule_max_temperature_celsius == Decimal("-15.00")
    assert shipment.rule_snapshot_json["name"] == "mRNA-1273 Deep Freeze"

    # Profile must now be locked
    db.refresh(profile_a)
    assert profile_a.is_locked is True


def test_shipment_lifecycle_state_machine(shipment_db):
    """Verify state transitions CREATED -> IN_TRANSIT -> DELIVERED -> VERIFIED and rejection of invalid jumps."""
    db = shipment_db["db"]
    org_a = shipment_db["org_a"]
    admin_a = shipment_db["admin_a"]
    profile_a = shipment_db["profile_a"]

    shipment = shipment_service.create_shipment(
        db=db,
        org_id=org_a.id,
        product_profile_id=profile_a.id,
        tracking_number="PFIZ-2026-0002",
        origin="Site A",
        destination="Site B",
        created_by_user_id=admin_a.id,
    )

    # Invalid jump: CREATED -> DELIVERED directly must fail
    with pytest.raises(HTTPException) as exc_invalid:
        shipment_service.update_shipment_status(
            db=db,
            org_id=org_a.id,
            shipment_id=shipment.id,
            new_status=ShipmentStatus.DELIVERED,
        )
    assert exc_invalid.value.status_code == 400
    assert "Invalid state transition" in exc_invalid.value.detail

    # Transition 1: CREATED -> IN_TRANSIT
    in_transit = shipment_service.update_shipment_status(
        db=db,
        org_id=org_a.id,
        shipment_id=shipment.id,
        new_status=ShipmentStatus.IN_TRANSIT,
    )
    assert in_transit.status == ShipmentStatus.IN_TRANSIT
    assert in_transit.dispatched_at is not None

    # Transition 2: IN_TRANSIT -> DELIVERED
    delivered = shipment_service.update_shipment_status(
        db=db,
        org_id=org_a.id,
        shipment_id=shipment.id,
        new_status=ShipmentStatus.DELIVERED,
    )
    assert delivered.status == ShipmentStatus.DELIVERED
    assert delivered.delivered_at is not None

    # Transition 3: DELIVERED -> VERIFIED
    verified = shipment_service.update_shipment_status(
        db=db,
        org_id=org_a.id,
        shipment_id=shipment.id,
        new_status=ShipmentStatus.VERIFIED,
    )
    assert verified.status == ShipmentStatus.VERIFIED

    # Terminal state: VERIFIED -> IN_TRANSIT must fail
    with pytest.raises(HTTPException) as exc_terminal:
        shipment_service.update_shipment_status(
            db=db,
            org_id=org_a.id,
            shipment_id=shipment.id,
            new_status=ShipmentStatus.IN_TRANSIT,
        )
    assert exc_terminal.value.status_code == 400


def test_cross_tenant_shipment_isolation(shipment_db):
    """Verify tenant isolation: Org B cannot access, transition, or use Org A's profiles or shipments."""
    db = shipment_db["db"]
    org_a = shipment_db["org_a"]
    admin_a = shipment_db["admin_a"]
    profile_a = shipment_db["profile_a"]
    org_b = shipment_db["org_b"]
    admin_b = shipment_db["admin_b"]

    # 1. Org B cannot create shipment using Org A's product profile
    with pytest.raises(HTTPException) as exc_profile:
        shipment_service.create_shipment(
            db=db,
            org_id=org_b.id,
            product_profile_id=profile_a.id,
            tracking_number="MOD-2026-0001",
            origin="Site X",
            destination="Site Y",
            created_by_user_id=admin_b.id,
        )
    assert exc_profile.value.status_code == 404

    # Create shipment in Org A
    shipment_a = shipment_service.create_shipment(
        db=db,
        org_id=org_a.id,
        product_profile_id=profile_a.id,
        tracking_number="PFIZ-2026-0003",
        origin="Site A",
        destination="Site B",
        created_by_user_id=admin_a.id,
    )

    # 2. Org B cannot retrieve Org A's shipment
    assert shipment_service.get_shipment_by_id(db=db, org_id=org_b.id, shipment_id=shipment_a.id) is None

    # 3. Org B cannot update Org A's shipment status
    with pytest.raises(HTTPException) as exc_update:
        shipment_service.update_shipment_status(
            db=db,
            org_id=org_b.id,
            shipment_id=shipment_a.id,
            new_status=ShipmentStatus.IN_TRANSIT,
        )
    assert exc_update.value.status_code == 404
