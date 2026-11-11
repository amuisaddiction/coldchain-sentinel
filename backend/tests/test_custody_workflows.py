"""Tests for Phase 8: Chain of Custody Handover Workflows and Tenant Security."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.database import Base
from app.models.enums import CustodyEventType, EvidenceType
from app.services import (
    organization_service,
    product_profile_service,
    shipment_service,
    custody_service,
    evidence_service,
)


@pytest.fixture
def custody_db():
    """Setup isolated test database seeded with organizations, shipment, and evidence."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    org_a, admin_a = organization_service.create_organization(
        db=db,
        name="AeroLogistics Bio",
        slug="aerologistics",
        admin_email="admin@aerologistics.com",
        admin_password="Password123!",
        admin_name="Aero Admin",
    )
    profile_a = product_profile_service.create_profile(
        db=db,
        org_id=org_a.id,
        name="Oncology Cold Pack",
        min_temp=Decimal("2.0"),
        max_temp=Decimal("8.0"),
        user_id=admin_a.id,
    )
    shipment_a = shipment_service.create_shipment(
        db=db,
        org_id=org_a.id,
        product_profile_id=profile_a.id,
        tracking_number="AERO-2026-CUSTODY",
        origin="Frankfurt Cargo City",
        destination="Singapore Changi Medical Hub",
        created_by_user_id=admin_a.id,
    )

    org_b, admin_b = organization_service.create_organization(
        db=db,
        name="Competitor Cargo",
        slug="competitor-cargo",
        admin_email="admin@competitor.com",
        admin_password="Password123!",
        admin_name="Comp Admin",
    )

    yield {
        "db": db,
        "org_a": org_a,
        "admin_a": admin_a,
        "shipment_a": shipment_a,
        "org_b": org_b,
        "admin_b": admin_b,
    }
    db.close()


def test_chain_of_custody_transfer_flow(custody_db):
    """Verify sequential recording of physical transfers across logistics stages."""
    db = custody_db["db"]
    org_a = custody_db["org_a"]
    admin_a = custody_db["admin_a"]
    shipment_a = custody_db["shipment_a"]

    now = datetime.now(timezone.utc)

    # 1. Dispatch
    ev1 = custody_service.record_custody_transfer(
        db=db,
        org_id=org_a.id,
        shipment_id=shipment_a.id,
        event_type=CustodyEventType.DISPATCH,
        carrier_name="Lufthansa Cargo",
        custodian_name="Capt. Hans Becker",
        location="Frankfurt FRA Hub",
        recorded_at=now,
        notes="Loaded into thermal container Unit 401",
        actor_user_id=admin_a.id,
    )
    assert ev1.id is not None
    assert ev1.event_type == CustodyEventType.DISPATCH

    # 2. Airport Transfer
    ev2 = custody_service.record_custody_transfer(
        db=db,
        org_id=org_a.id,
        shipment_id=shipment_a.id,
        event_type=CustodyEventType.AIRPORT_TRANSFER,
        carrier_name="Singapore Airlines Cargo",
        custodian_name="Ravi Kumar",
        location="Singapore SIN Cargo Area",
        recorded_at=now + timedelta(hours=12),
        actor_user_id=admin_a.id,
    )
    assert ev2.event_type == CustodyEventType.AIRPORT_TRANSFER

    # 3. Last Mile Pickup
    ev3 = custody_service.record_custody_transfer(
        db=db,
        org_id=org_a.id,
        shipment_id=shipment_a.id,
        event_type=CustodyEventType.LAST_MILE_PICKUP,
        carrier_name="PharmaExpress SG",
        custodian_name="Tan Wei Ming",
        location="SIN Ramp Gate 4",
        recorded_at=now + timedelta(hours=14),
        actor_user_id=admin_a.id,
    )

    # 4. Delivery Handover
    ev4 = custody_service.record_custody_transfer(
        db=db,
        org_id=org_a.id,
        shipment_id=shipment_a.id,
        event_type=CustodyEventType.DELIVERY_HANDOVER,
        carrier_name="PharmaExpress SG",
        custodian_name="Dr. Lee Mei Ling",
        location="Changi General Hospital Pharmacy",
        recorded_at=now + timedelta(hours=16),
        notes="Seal intact, signature collected",
        actor_user_id=admin_a.id,
    )

    # Verify chronological custody trail
    events = custody_service.list_custody_events(db=db, org_id=org_a.id, shipment_id=shipment_a.id)
    assert len(events) == 4
    assert [e.event_type for e in events] == [
        CustodyEventType.DISPATCH,
        CustodyEventType.AIRPORT_TRANSFER,
        CustodyEventType.LAST_MILE_PICKUP,
        CustodyEventType.DELIVERY_HANDOVER,
    ]


def test_cross_tenant_custody_isolation(custody_db):
    """Verify tenant isolation: Org B cannot record or view Org A's custody handovers."""
    db = custody_db["db"]
    shipment_a = custody_db["shipment_a"]
    org_b = custody_db["org_b"]
    admin_b = custody_db["admin_b"]

    # Org B cannot view Org A's custody trail
    events_b = custody_service.list_custody_events(db=db, org_id=org_b.id, shipment_id=shipment_a.id)
    assert len(events_b) == 0

    # Org B cannot append a custody event to Org A's shipment
    with pytest.raises(HTTPException) as exc:
        custody_service.record_custody_transfer(
            db=db,
            org_id=org_b.id,
            shipment_id=shipment_a.id,
            event_type=CustodyEventType.DISPATCH,
            carrier_name="Rogue Carrier",
            custodian_name="Attacker",
            location="Unknown",
            actor_user_id=admin_b.id,
        )
    assert exc.value.status_code == 404
