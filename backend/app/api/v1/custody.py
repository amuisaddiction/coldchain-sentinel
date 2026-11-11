"""Chain of custody transfer API router."""

from typing import List
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_current_active_user,
    require_operator_or_above,
    get_client_ip,
)
from app.models.user import User
from app.schemas.custody import (
    CustodyEventCreate,
    CustodyEventResponse,
)
from app.services import custody_service

router = APIRouter(prefix="/shipments/{shipment_id}/custody", tags=["Chain of Custody"])


@router.get("/", response_model=List[CustodyEventResponse])
def get_custody_trail(
    shipment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve the chronological custody handover audit trail for a shipment."""
    return custody_service.list_custody_events(
        db=db,
        org_id=current_user.organization_id,
        shipment_id=shipment_id,
    )


@router.post("/", response_model=CustodyEventResponse, status_code=status.HTTP_201_CREATED)
def record_custody_event(
    request: Request,
    shipment_id: str,
    payload: CustodyEventCreate,
    current_user: User = Depends(require_operator_or_above),
    db: Session = Depends(get_db),
):
    """Record a verified physical handover checkpoint in the shipment chain of custody."""
    client_ip = get_client_ip(request)
    return custody_service.record_custody_transfer(
        db=db,
        org_id=current_user.organization_id,
        shipment_id=shipment_id,
        event_type=payload.event_type,
        carrier_name=payload.carrier_name,
        custodian_name=payload.custodian_name,
        location=payload.location,
        recorded_at=payload.recorded_at,
        evidence_file_id=payload.evidence_file_id,
        notes=payload.notes,
        actor_user_id=current_user.id,
        client_ip=client_ip,
    )
