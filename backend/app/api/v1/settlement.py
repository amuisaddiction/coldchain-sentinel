"""API router for ColdChain AI Settlement Intelligence."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_and_verify_token
from app.models.user import User
from app.schemas.contract_intelligence import (
    PharmaContract,
    ContractExtractionRequest,
    ContractExtractionResponse,
    SettlementInvestigationResult,
    HumanApprovalRequest,
    SettlementExecutionResponse,
)
from app.services.contract_service import contract_service
from app.services.settlement_service import settlement_service

router = APIRouter(prefix="/settlement", tags=["AI Settlement Intelligence"])


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Resolve authenticated user if Bearer token present; allows unauthenticated demo exploration."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    try:
        claims = decode_and_verify_token(token, expected_type="access")
        user_id = claims.get("sub")
        org_id = claims.get("org_id")
        return db.scalar(
            select(User).where(
                User.id == user_id,
                User.organization_id == org_id,
                User.is_active == True,
            )
        )
    except Exception:
        return None


@router.get("/contracts/samples", response_model=List[PharmaContract])
def get_sample_contracts(
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Retrieve curated pharmaceutical freight master service agreements."""
    return contract_service.get_sample_contracts()


@router.post("/contracts/extract", response_model=ContractExtractionResponse)
def extract_contract(
    req: ContractExtractionRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Extract temperature boundaries, deadlines, quality terms, and penalty rules from a contract."""
    return contract_service.extract_contract(
        contract_text=req.contract_text,
        sample_id=req.sample_id,
    )


@router.post("/investigate/{shipment_identifier}", response_model=SettlementInvestigationResult)
def run_settlement_investigation(
    shipment_identifier: str,
    contract_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Conduct AI comparative investigation matching contract conditions against telemetry, hashes, and custody."""
    org_id = current_user.organization_id if current_user else "org-demo-default"
    return settlement_service.run_investigation(
        db=db,
        org_id=org_id,
        shipment_identifier=shipment_identifier,
        contract_id=contract_id,
    )


@router.post("/approve", response_model=SettlementExecutionResponse)
def approve_settlement(
    req: HumanApprovalRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Execute human-approved settlement release or quality hold via PayPal."""
    if current_user:
        org_id = current_user.organization_id
        req.reviewer_id = current_user.email
        is_demo = False
    else:
        org_id = "org-demo-default"
        req.reviewer_id = "DEMO-REVIEWER-ANONYMOUS"
        is_demo = True

    return settlement_service.execute_human_approval(
        db=db,
        org_id=org_id,
        approval_req=req,
        is_demo_user=is_demo,
    )
