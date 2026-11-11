"""Payment service managing authorization, human-verified capture, idempotency, and outbox staging."""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.currency import get_currency_exponent, decimal_str_to_minor, minor_to_decimal_str
from app.core.idempotency import generate_payment_idempotency_key
from app.models.payment import Payment, PaymentIdempotencyRecord
from app.models.shipment import Shipment
from app.models.outbox import OutboxEvent
from app.models.enums import PaymentStatus, PaymentAction, IdempotencyStatus, ShipmentStatus, OutboxStatus
from app.services.paypal_client import paypal_client
from app.services.audit_service import log_audit_event


def get_payment_by_id(db: Session, org_id: str, payment_id: str) -> Optional[Payment]:
    """Retrieve payment strictly scoped to caller's organization."""
    return db.scalar(
        select(Payment).where(
            Payment.organization_id == org_id,
            Payment.id == payment_id,
        )
    )


def get_payment_by_shipment_id(db: Session, org_id: str, shipment_id: str) -> Optional[Payment]:
    """Retrieve payment for a specific shipment."""
    return db.scalar(
        select(Payment).where(
            Payment.organization_id == org_id,
            Payment.shipment_id == shipment_id,
        )
    )


def list_payments(db: Session, org_id: str, skip: int = 0, limit: int = 50) -> List[Payment]:
    """List payments for caller's organization."""
    return list(
        db.scalars(
            select(Payment)
            .where(Payment.organization_id == org_id)
            .offset(skip)
            .limit(limit)
            .order_by(Payment.created_at.desc())
        ).all()
    )


def create_payment(
    db: Session,
    org_id: str,
    shipment_id: str,
    amount: Decimal,
    currency: str = "USD",
    paypal_order_id: Optional[str] = None,
    paypal_auth_id: Optional[str] = None,
    user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> Payment:
    """Create an authorized payment record tied to a shipment."""
    shipment = db.scalar(
        select(Shipment).where(
            Shipment.organization_id == org_id,
            Shipment.id == shipment_id,
        )
    )
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found in your organization",
        )

    # Check for existing payment on this shipment
    existing_payment = db.scalar(select(Payment).where(Payment.shipment_id == shipment_id))
    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A payment record already exists for this shipment",
        )

    exponent = get_currency_exponent(currency)
    amount_str = f"{amount:.{exponent}f}"
    minor_units = decimal_str_to_minor(amount_str, exponent)

    auth_id = paypal_auth_id or f"AUTH-SANDBOX-{uuid.uuid4().hex[:12].upper()}"
    order_id = paypal_order_id or f"ORDER-{uuid.uuid4().hex[:12].upper()}"

    now = datetime.now(timezone.utc)
    payment = Payment(
        id=str(uuid.uuid4()),
        shipment_id=shipment.id,
        organization_id=org_id,
        payment_provider="PAYPAL",
        paypal_order_id=order_id,
        paypal_authorization_id=auth_id,
        amount_minor=minor_units,
        currency=currency.upper(),
        currency_exponent=exponent,
        status=PaymentStatus.AUTHORIZED,
        authorized_at=now,
    )
    db.add(payment)
    db.flush()

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=user_id,
        shipment_id=shipment.id,
        entity_type="PAYMENT",
        entity_id=payment.id,
        action="PAYMENT_AUTHORIZE",
        payload_after={
            "auth_id": auth_id,
            "amount_minor": minor_units,
            "currency": currency,
        },
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(payment)
    return payment


def request_capture(
    db: Session,
    org_id: str,
    payment_id: str,
    user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> OutboxEvent:
    """
    Request payment capture after verifying human compliance approval.
    Stages a reliable OutboxEvent for transactional execution.
    """
    payment = get_payment_by_id(db, org_id, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found in your organization",
        )

    # Human-approval and compliance check: Shipment MUST be in VERIFIED status!
    shipment = db.scalar(select(Shipment).where(Shipment.id == payment.shipment_id))
    if not shipment or shipment.status != ShipmentStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment capture rejected: Shipment compliance has not been verified",
        )

    if payment.status != PaymentStatus.AUTHORIZED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment cannot be captured in status {payment.status.value}",
        )

    # Generate stable idempotency key
    idempotency_key = generate_payment_idempotency_key(
        shipment_ref=shipment.tracking_number,
        action="CAPTURE",
        authorization_id=payment.paypal_authorization_id or "",
    )

    # Check or create idempotency record
    idemp_rec = db.scalar(
        select(PaymentIdempotencyRecord).where(
            PaymentIdempotencyRecord.provider == "PAYPAL",
            PaymentIdempotencyRecord.action == PaymentAction.CAPTURE,
            PaymentIdempotencyRecord.idempotency_key == idempotency_key,
        )
    )
    now = datetime.now(timezone.utc)
    if not idemp_rec:
        idemp_rec = PaymentIdempotencyRecord(
            id=str(uuid.uuid4()),
            provider="PAYPAL",
            action=PaymentAction.CAPTURE,
            idempotency_key=idempotency_key,
            organization_id=org_id,
            payment_id=payment.id,
            status=IdempotencyStatus.IN_PROGRESS,
            request_hash=idempotency_key[-16:],
            expires_at=now + timedelta(days=7),
        )
        db.add(idemp_rec)
        db.flush()

    # Enqueue Outbox event
    outbox_event = OutboxEvent(
        id=str(uuid.uuid4()),
        event_type="PAYMENT_CAPTURE",
        aggregate_type="PAYMENT",
        aggregate_id=payment.id,
        payload={
            "payment_id": payment.id,
            "organization_id": org_id,
            "idempotency_key": idempotency_key,
        },
        status=OutboxStatus.PENDING,
        available_at=now,
    )
    db.add(outbox_event)

    payment.status = PaymentStatus.HELD_FOR_REVIEW

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=user_id,
        shipment_id=shipment.id,
        entity_type="PAYMENT",
        entity_id=payment.id,
        action="PAYMENT_CAPTURE_REQUESTED",
        payload_after={"idempotency_key": idempotency_key, "outbox_id": outbox_event.id},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(outbox_event)
    return outbox_event


def execute_capture(
    db: Session,
    payment_id: str,
    idempotency_key: str,
    client_ip: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute physical capture with PayPal REST API using idempotency protection."""
    payment = db.scalar(select(Payment).where(Payment.id == payment_id))
    if not payment:
        raise ValueError(f"Payment {payment_id} not found")

    amount_decimal = minor_to_decimal_str(payment.amount_minor, payment.currency_exponent)

    # Call PayPal client
    resp = paypal_client.capture_authorization(
        authorization_id=payment.paypal_authorization_id,
        amount_decimal=amount_decimal,
        currency=payment.currency,
        idempotency_key=idempotency_key,
    )

    capture_id = resp.get("id")
    now = datetime.now(timezone.utc)

    payment.paypal_capture_id = capture_id
    payment.status = PaymentStatus.CAPTURED
    payment.settled_at = now

    # Update idempotency record
    idemp_rec = db.scalar(
        select(PaymentIdempotencyRecord).where(
            PaymentIdempotencyRecord.provider == "PAYPAL",
            PaymentIdempotencyRecord.action == PaymentAction.CAPTURE,
            PaymentIdempotencyRecord.idempotency_key == idempotency_key,
        )
    )
    if idemp_rec:
        idemp_rec.status = IdempotencyStatus.SUCCESS
        idemp_rec.response_payload = resp
        idemp_rec.response_status_code = 201

    log_audit_event(
        db=db,
        organization_id=payment.organization_id,
        shipment_id=payment.shipment_id,
        entity_type="PAYMENT",
        entity_id=payment.id,
        action="PAYMENT_CAPTURE_SETTLED",
        payload_after={"capture_id": capture_id, "status": "CAPTURED"},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(payment)
    return resp
