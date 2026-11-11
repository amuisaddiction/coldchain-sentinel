"""Investigations and incident reporting API router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status, Request, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_current_active_user,
    require_manager_or_admin,
    get_client_ip,
)
from app.models.user import User
from app.models.enums import InvestigationStatus
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationUpdate,
    InvestigationResponse,
    InvestigationReportResponse,
)
from app.services import investigation_service

router = APIRouter(prefix="/investigations", tags=["Investigations & Incident Reports"])


@router.get("/", response_model=List[InvestigationResponse])
def list_investigations(
    status: Optional[InvestigationStatus] = Query(None, description="Optional status filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List investigations for caller's organization."""
    return investigation_service.list_investigations(
        db=db,
        org_id=current_user.organization_id,
        status_filter=status,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)
def open_investigation(
    request: Request,
    payload: InvestigationCreate,
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Open a new formal investigation inquiry into a shipment anomaly or excursion."""
    client_ip = get_client_ip(request)
    return investigation_service.create_investigation(
        db=db,
        org_id=current_user.organization_id,
        shipment_id=payload.shipment_id,
        priority=payload.priority,
        assigned_to=payload.assigned_to,
        findings=payload.findings,
        actor_user_id=current_user.id,
        client_ip=client_ip,
    )


@router.get("/{investigation_id}", response_model=InvestigationResponse)
def get_investigation(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve investigation details."""
    inv = investigation_service.get_investigation_by_id(
        db=db,
        org_id=current_user.organization_id,
        investigation_id=investigation_id,
    )
    if not inv:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found in your organization",
        )
    return inv


@router.put("/{investigation_id}", response_model=InvestigationResponse)
def update_investigation(
    request: Request,
    investigation_id: str,
    payload: InvestigationUpdate,
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Update investigation status, assign investigator, and record resolution findings."""
    client_ip = get_client_ip(request)
    return investigation_service.update_investigation(
        db=db,
        org_id=current_user.organization_id,
        investigation_id=investigation_id,
        new_status=payload.status,
        new_priority=payload.priority,
        assigned_to=payload.assigned_to,
        findings=payload.findings,
        resolution_summary=payload.resolution_summary,
        actor_user_id=current_user.id,
        client_ip=client_ip,
    )


@router.get("/{investigation_id}/report", response_model=InvestigationReportResponse)
def get_investigation_report(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Compile and retrieve comprehensive incident report with real evidence and compliance telemetry."""
    return investigation_service.generate_investigation_report(
        db=db,
        org_id=current_user.organization_id,
        investigation_id=investigation_id,
    )
