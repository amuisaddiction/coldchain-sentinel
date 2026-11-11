"""Tests for Phase 11 & 12: Carrier Intelligence and Sentinel Challenge."""

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.enums import CustodyEventType, DecisionType
from app.services import (
    organization_service,
    product_profile_service,
    shipment_service,
    custody_service,
    carrier_service,
    challenge_service,
)


@pytest.fixture
def challenge_db():
    """Setup isolated test database seeded with organization."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    org, admin = organization_service.create_organization(
        db=db,
        name="Global Pharma Challenge",
        slug="global-pharma-challenge",
        admin_email="admin@challenge.com",
        admin_password="Password123!",
        admin_name="Challenge Admin",
    )

    yield {
        "db": db,
        "org": org,
        "admin": admin,
    }
    db.close()


def test_carrier_intelligence_scoring(challenge_db):
    """Verify carrier intelligence computes transparent metrics and flags sample size warnings."""
    db = challenge_db["db"]
    org = challenge_db["org"]
    admin = challenge_db["admin"]

    profile = product_profile_service.create_profile(
        db=db,
        org_id=org.id,
        name="Carrier Test Profile",
        min_temp=Decimal("2.0"),
        max_temp=Decimal("8.0"),
        user_id=admin.id,
    )

    # Create 2 shipments handled by "DHL Global Forwarding"
    s1 = shipment_service.create_shipment(
        db=db, org_id=org.id, product_profile_id=profile.id,
        tracking_number="DHL-001", origin="FRA", destination="JFK",
        created_by_user_id=admin.id,
    )
    s2 = shipment_service.create_shipment(
        db=db, org_id=org.id, product_profile_id=profile.id,
        tracking_number="DHL-002", origin="FRA", destination="ORD",
        created_by_user_id=admin.id,
    )

    custody_service.record_custody_transfer(
        db=db, org_id=org.id, shipment_id=s1.id, event_type=CustodyEventType.DISPATCH,
        carrier_name="DHL Global Forwarding", custodian_name="Officer Schmidt", location="FRA Cargo",
        actor_user_id=admin.id,
    )
    custody_service.record_custody_transfer(
        db=db, org_id=org.id, shipment_id=s2.id, event_type=CustodyEventType.DISPATCH,
        carrier_name="DHL Global Forwarding", custodian_name="Officer Weber", location="FRA Cargo",
        actor_user_id=admin.id,
    )

    summary = carrier_service.get_carrier_scores(db=db, org_id=org.id)
    assert summary.total_carriers_tracked == 1
    dhl = summary.carriers[0]
    assert dhl.carrier_name == "DHL Global Forwarding"
    assert dhl.total_shipments == 2
    # 2 shipments is < 5, so sample size warning must be True!
    assert dhl.sample_size_warning is True
    assert "Low sample size warning" in dhl.sample_size_note


def test_sentinel_challenge_deterministic_scenarios(challenge_db):
    """Verify Sentinel Challenge initializes all 4 reproducible hackathon demo scenarios."""
    db = challenge_db["db"]
    org = challenge_db["org"]
    admin = challenge_db["admin"]

    scenarios = challenge_service.reset_challenge(
        db=db,
        org_id=org.id,
        user_id=admin.id,
    )

    assert len(scenarios) == 4
    scenario_ids = [s.scenario_id for s in scenarios]
    assert "clean-shipment" in scenario_ids
    assert "thermal-excursion" in scenario_ids
    assert "evidence-tamper" in scenario_ids
    assert "custody-gap" in scenario_ids

    # Scenario 1 (Clean) must be CAPTURED
    clean = next(s for s in scenarios if s.scenario_id == "clean-shipment")
    assert clean.verification_decision == "PASSED"
    assert clean.payment_status == "CAPTURED"

    # Scenario 2 (Excursion) must be FAILED and capture blocked
    excursion = next(s for s in scenarios if s.scenario_id == "thermal-excursion")
    assert excursion.verification_decision == "FAILED"
    assert "CAPTURE_BLOCKED" in excursion.payment_status
