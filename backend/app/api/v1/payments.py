"""Payment assurance API router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_current_active_user,
    require_manager_or_admin,
    get_client_ip,
)
from app.models.user import User
from app.core.currency import minor_to_decimal_str
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentCaptureRequest,
)
from app.services import payment_service, outbox_dispatcher

router = APIRouter(tags=["Payment Assurance"])


def _to_response(payment) -> PaymentResponse:
    """Format Payment ORM object to API response schema."""
    amount_dec = minor_to_decimal_str(payment.amount_minor, payment.currency_exponent)
    return PaymentResponse(
        id=payment.id,
        shipment_id=payment.shipment_id,
        organization_id=payment.organization_id,
        payment_provider=payment.payment_provider,
        paypal_order_id=payment.paypal_order_id,
        paypal_authorization_id=payment.paypal_authorization_id,
        paypal_capture_id=payment.paypal_capture_id,
        amount_minor=payment.amount_minor,
        amount_decimal=amount_dec,
        currency=payment.currency,
        currency_exponent=payment.currency_exponent,
        status=payment.status,
        authorized_at=payment.authorized_at,
        settled_at=payment.settled_at,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


@router.get("/payments/", response_model=List[PaymentResponse])
def list_payments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List payment assurance records for caller's organization."""
    payments = payment_service.list_payments(db=db, org_id=current_user.organization_id)
    return [_to_response(p) for p in payments]


@router.get("/shipments/{shipment_id}/payment", response_model=Optional[PaymentResponse])
def get_shipment_payment(
    shipment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve payment assurance record for a shipment."""
    payment = payment_service.get_payment_by_shipment_id(
        db=db,
        org_id=current_user.organization_id,
        shipment_id=shipment_id,
    )
    if not payment:
        return None
    return _to_response(payment)


@router.post("/shipments/{shipment_id}/payment", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment_payment(
    request: Request,
    shipment_id: str,
    payload: PaymentCreate,
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Create an authorized payment record tied to a cold-chain shipment."""
    client_ip = get_client_ip(request)
    payment = payment_service.create_payment(
        db=db,
        org_id=current_user.organization_id,
        shipment_id=shipment_id,
        amount=payload.amount,
        currency=payload.currency,
        paypal_order_id=payload.paypal_order_id,
        paypal_auth_id=payload.paypal_authorization_id,
        user_id=current_user.id,
        client_ip=client_ip,
    )
    return _to_response(payment)


@router.post("/payments/{payment_id}/capture", response_model=PaymentResponse)
def capture_payment(
    request: Request,
    payment_id: str,
    payload: Optional[PaymentCaptureRequest] = None,
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """
    Approve and capture authorized payment.
    Requires that shipment compliance is verified (human-approval rule).
    Enqueues outbox event and immediately processes through dispatcher.
    """
    client_ip = get_client_ip(request)
    outbox_event = payment_service.request_capture(
        db=db,
        org_id=current_user.organization_id,
        payment_id=payment_id,
        user_id=current_user.id,
        client_ip=client_ip,
    )

    # Process outbox queue synchronously for immediate feedback
    outbox_dispatcher.run_outbox_cycle(db=db)

    # Return refreshed payment
    payment = payment_service.get_payment_by_id(
        db=db,
        org_id=current_user.organization_id,
        payment_id=payment_id,
    )
    return _to_response(payment)
