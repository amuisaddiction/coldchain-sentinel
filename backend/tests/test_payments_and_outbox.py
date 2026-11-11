"""Tests for Phase 9: PayPal Sandbox Integration, Human-Approval Verification Gate, and Reliable Outbox Dispatcher."""

from decimal import Decimal
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.database import Base
from app.models.enums import (
    ShipmentStatus,
    PaymentStatus,
    IdempotencyStatus,
    OutboxStatus,
)
from app.models.payment import Payment, PaymentIdempotencyRecord
from app.models.outbox import OutboxEvent
from app.services import (
    organization_service,
    product_profile_service,
    shipment_service,
    payment_service,
    outbox_dispatcher,
)


@pytest.fixture
def payment_db():
    """Setup isolated test database seeded with organization, profile, and shipment."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    org, admin = organization_service.create_organization(
        db=db,
        name="BioPay Assurance Corp",
        slug="biopay",
        admin_email="admin@biopay.com",
        admin_password="Password123!",
        admin_name="BioPay Admin",
    )
    profile = product_profile_service.create_profile(
        db=db,
        org_id=org.id,
        name="Cold Storage Plasma",
        min_temp=Decimal("-20.00"),
        max_temp=Decimal("-10.00"),
        user_id=admin.id,
    )
    shipment = shipment_service.create_shipment(
        db=db,
        org_id=org.id,
        product_profile_id=profile.id,
        tracking_number="PAY-2026-TEST",
        origin="Facility A",
        destination="Facility B",
        created_by_user_id=admin.id,
    )

    yield {
        "db": db,
        "org": org,
        "admin": admin,
        "profile": profile,
        "shipment": shipment,
    }
    db.close()


def test_payment_creation_and_currency_exponent(payment_db):
    """Verify payment creation calculates correct minor units ($15,000.50 USD = 1500050 cents)."""
    db = payment_db["db"]
    org = payment_db["org"]
    admin = payment_db["admin"]
    shipment = payment_db["shipment"]

    payment = payment_service.create_payment(
        db=db,
        org_id=org.id,
        shipment_id=shipment.id,
        amount=Decimal("15000.50"),
        currency="USD",
        user_id=admin.id,
    )
    assert payment.id is not None
    assert payment.amount_minor == 1500050
    assert payment.currency == "USD"
    assert payment.currency_exponent == 2
    assert payment.status == PaymentStatus.AUTHORIZED
    assert payment.paypal_authorization_id.startswith("AUTH-")


def test_capture_blocked_before_compliance_verification(payment_db):
    """Verify payment capture is strictly blocked with HTTP 400 if shipment is NOT VERIFIED."""
    db = payment_db["db"]
    org = payment_db["org"]
    admin = payment_db["admin"]
    shipment = payment_db["shipment"]

    payment = payment_service.create_payment(
        db=db,
        org_id=org.id,
        shipment_id=shipment.id,
        amount=Decimal("2500.00"),
        currency="USD",
        user_id=admin.id,
    )

    # Shipment is in CREATED status (unverified)
    assert shipment.status == ShipmentStatus.CREATED

    with pytest.raises(HTTPException) as exc:
        payment_service.request_capture(
            db=db,
            org_id=org.id,
            payment_id=payment.id,
            user_id=admin.id,
        )
    assert exc.value.status_code == 400
    assert "Shipment compliance has not been verified" in exc.value.detail


def test_verified_shipment_capture_and_outbox_dispatch(payment_db):
    """Verify complete end-to-end payment capture: verification -> outbox staging -> dispatcher execution."""
    db = payment_db["db"]
    org = payment_db["org"]
    admin = payment_db["admin"]
    shipment = payment_db["shipment"]

    payment = payment_service.create_payment(
        db=db,
        org_id=org.id,
        shipment_id=shipment.id,
        amount=Decimal("5000.00"),
        currency="USD",
        user_id=admin.id,
    )

    # Progress shipment to VERIFIED status
    shipment_service.update_shipment_status(db=db, org_id=org.id, shipment_id=shipment.id, new_status=ShipmentStatus.IN_TRANSIT)
    shipment_service.update_shipment_status(db=db, org_id=org.id, shipment_id=shipment.id, new_status=ShipmentStatus.DELIVERED)
    shipment_service.update_shipment_status(db=db, org_id=org.id, shipment_id=shipment.id, new_status=ShipmentStatus.VERIFIED)

    # Request capture
    outbox_event = payment_service.request_capture(
        db=db,
        org_id=org.id,
        payment_id=payment.id,
        user_id=admin.id,
    )
    assert outbox_event.event_type == "PAYMENT_CAPTURE"
    assert outbox_event.status == OutboxStatus.PENDING

    # Run outbox processing cycle
    processed_count = outbox_dispatcher.run_outbox_cycle(db=db)
    assert processed_count == 1

    # Verify outbox event completed
    db.refresh(outbox_event)
    assert outbox_event.status == OutboxStatus.COMPLETED
    assert outbox_event.processed_at is not None

    # Verify payment settled
    db.refresh(payment)
    assert payment.status == PaymentStatus.CAPTURED
    assert payment.paypal_capture_id is not None
    assert payment.paypal_capture_id.startswith(("CAP-SANDBOX-", "SIMULATED-PAYPAL-CAP-"))
    assert payment.settled_at is not None

    # Verify idempotency record updated to SUCCESS
    idemp_rec = db.scalar(
        select(PaymentIdempotencyRecord).where(
            PaymentIdempotencyRecord.payment_id == payment.id
        )
    )
    assert idemp_rec is not None
    assert idemp_rec.status == IdempotencyStatus.SUCCESS


def test_outbox_lease_expiration_and_fencing(payment_db):
    """Verify expired lease recovery and that stale workers cannot overwrite reclaimed events."""
    db = payment_db["db"]
    now = datetime.now(timezone.utc)

    # Create an event directly in PROCESSING with an expired lease
    ev = OutboxEvent(
        id="test-event-expired",
        event_type="PAYMENT_CAPTURE",
        aggregate_type="PAYMENT",
        aggregate_id="dummy-agg",
        payload={"dummy": True},
        status=OutboxStatus.PROCESSING,
        available_at=now - timedelta(minutes=5),
        claim_token="stale-worker-token",
        lease_until=now - timedelta(seconds=10),  # Lease expired 10s ago
        attempts=1,
    )
    db.add(ev)
    db.commit()

    # Worker 2 claims the event
    claimed = outbox_dispatcher.claim_pending_events(db=db)
    assert len(claimed) == 1
    reclaimed_ev, new_token = claimed[0]
    assert new_token != "stale-worker-token"
    assert reclaimed_ev.claim_token == new_token

    # Stale Worker 1 attempts to process with old token -> MUST BE REJECTED by fencing!
    rejection = outbox_dispatcher.process_claimed_event(
        db=db,
        event_id="test-event-expired",
        claim_token="stale-worker-token",
    )
    assert rejection is False
