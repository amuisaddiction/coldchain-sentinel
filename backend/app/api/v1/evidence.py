"""Evidence upload and trust engine verification API router."""

from typing import List
from fastapi import APIRouter, Depends, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_current_active_user,
    require_operator_or_above,
    get_client_ip,
)
from app.models.user import User
from app.models.enums import EvidenceType
from app.schemas.evidence import (
    EvidenceFileResponse,
    EvidenceVerificationResponse,
)
from app.services import evidence_service

router = APIRouter(tags=["Evidence Trust Engine"])


@router.get("/shipments/{shipment_id}/evidence", response_model=List[EvidenceFileResponse])
def list_shipment_evidence(
    shipment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all evidence files uploaded for a shipment."""
    return evidence_service.list_evidence_for_shipment(
        db=db,
        org_id=current_user.organization_id,
        shipment_id=shipment_id,
    )


@router.post("/shipments/{shipment_id}/evidence", response_model=EvidenceFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    request: Request,
    shipment_id: str,
    file_type: EvidenceType = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_operator_or_above),
    db: Session = Depends(get_db),
):
    """Upload evidence file, calculate cryptographic SHA-256 hash, and extract telemetry."""
    client_ip = get_client_ip(request)
    content = await file.read()
    return evidence_service.upload_evidence(
        db=db,
        org_id=current_user.organization_id,
        shipment_id=shipment_id,
        file_type=file_type,
        original_filename=file.filename or "evidence.dat",
        content=content,
        uploaded_by_user_id=current_user.id,
        client_ip=client_ip,
    )


@router.post("/evidence/{evidence_id}/verify", response_model=EvidenceVerificationResponse)
def verify_evidence(
    request: Request,
    evidence_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Verify stored evidence file against recorded cryptographic SHA-256 digest to detect tampering."""
    client_ip = get_client_ip(request)
    return evidence_service.verify_evidence_integrity(
        db=db,
        org_id=current_user.organization_id,
        evidence_id=evidence_id,
        client_ip=client_ip,
    )
