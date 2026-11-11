"""Shipment management API router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status, Request, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_current_active_user,
    require_operator_or_above,
    get_client_ip,
)
from app.models.user import User
from app.models.enums import ShipmentStatus
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentResponse,
    ShipmentStatusUpdate,
)
from app.services import shipment_service

router = APIRouter(prefix="/shipments", tags=["Shipments"])


@router.get("/", response_model=List[ShipmentResponse])
def list_shipments(
    status: Optional[ShipmentStatus] = Query(None, description="Optional status filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List shipments in caller's organization."""
    return shipment_service.list_shipments(
        db=db,
        org_id=current_user.organization_id,
        status_filter=status,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(
    request: Request,
    payload: ShipmentCreate,
    current_user: User = Depends(require_operator_or_above),
    db: Session = Depends(get_db),
):
    """Create a new shipment with an immutable rule snapshot."""
    client_ip = get_client_ip(request)
    return shipment_service.create_shipment(
        db=db,
        org_id=current_user.organization_id,
        product_profile_id=payload.product_profile_id,
        tracking_number=payload.tracking_number,
        origin=payload.origin,
        destination=payload.destination,
        created_by_user_id=current_user.id,
        client_ip=client_ip,
    )


@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(
    shipment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve shipment details."""
    shipment = shipment_service.get_shipment_by_id(
        db=db,
        org_id=current_user.organization_id,
        shipment_id=shipment_id,
    )
    if not shipment:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found in your organization",
        )
    return shipment


@router.put("/{shipment_id}/status", response_model=ShipmentResponse)
def update_shipment_status(
    request: Request,
    shipment_id: str,
    payload: ShipmentStatusUpdate,
    current_user: User = Depends(require_operator_or_above),
    db: Session = Depends(get_db),
):
    """Transition shipment lifecycle status with state machine enforcement."""
    client_ip = get_client_ip(request)
    return shipment_service.update_shipment_status(
        db=db,
        org_id=current_user.organization_id,
        shipment_id=shipment_id,
        new_status=payload.status,
        actor_user_id=current_user.id,
        client_ip=client_ip,
    )
