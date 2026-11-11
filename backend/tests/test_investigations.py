"""Tests for Phase 10: Investigations and Incident Report Generation."""

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.enums import InvestigationStatus, InvestigationPriority
from app.services import (
    organization_service,
    product_profile_service,
    shipment_service,
    investigation_service,
)


@pytest.fixture
def inv_db():
    """Setup isolated test database seeded with organization and shipment."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    org, admin = organization_service.create_organization(
        db=db,
        name="BioShield Diagnostics",
        slug="bioshield",
        admin_email="admin@bioshield.com",
        admin_password="Password123!",
        admin_name="Bio Admin",
    )
    profile = product_profile_service.create_profile(
        db=db,
        org_id=org.id,
        name="Diagnostics Reagents",
        min_temp=Decimal("2.0"),
        max_temp=Decimal("8.0"),
        user_id=admin.id,
    )
    shipment = shipment_service.create_shipment(
        db=db,
        org_id=org.id,
        product_profile_id=profile.id,
        tracking_number="INV-2026-TEST",
        origin="Paris Hub",
        destination="Marseille Clinic",
        created_by_user_id=admin.id,
    )

    yield {
        "db": db,
        "org": org,
        "admin": admin,
        "shipment": shipment,
    }
    db.close()


def test_investigation_lifecycle_and_report_generation(inv_db):
    """Verify investigation creation, update, and real data report generation."""
    db = inv_db["db"]
    org = inv_db["org"]
    admin = inv_db["admin"]
    shipment = inv_db["shipment"]

    # 1. Open investigation
    inv = investigation_service.create_investigation(
        db=db,
        org_id=org.id,
        shipment_id=shipment.id,
        priority=InvestigationPriority.HIGH,
        assigned_to=admin.id,
        findings="Telemetry shows potential container breach during flight.",
        actor_user_id=admin.id,
    )
    assert inv.id is not None
    assert inv.status == InvestigationStatus.OPEN
    assert inv.priority == InvestigationPriority.HIGH

    # 2. Update and resolve investigation
    updated = investigation_service.update_investigation(
        db=db,
        org_id=org.id,
        investigation_id=inv.id,
        new_status=InvestigationStatus.RESOLVED_REJECTED,
        resolution_summary="Dry ice sublimation confirmed. Temperature exceeded 15C. Lot rejected.",
        actor_user_id=admin.id,
    )
    assert updated.status == InvestigationStatus.RESOLVED_REJECTED
    assert updated.resolved_at is not None

    # 3. Generate comprehensive incident report
    report = investigation_service.generate_investigation_report(
        db=db,
        org_id=org.id,
        investigation_id=inv.id,
    )
    assert report["investigation_id"] == inv.id
    assert report["tracking_number"] == "INV-2026-TEST"
    assert report["status"] == InvestigationStatus.RESOLVED_REJECTED
    assert "Dry ice sublimation confirmed" in report["resolution_summary"]
    assert "shipment_details" in report
    assert "temperature_summary" in report
    assert "evidence_artifacts" in report
    assert "verification_decisions" in report
