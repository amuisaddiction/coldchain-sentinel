"""Carrier intelligence API router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.carrier import CarrierIntelligenceSummary
from app.services import carrier_service

router = APIRouter(prefix="/carrier-intelligence", tags=["Carrier Intelligence"])


@router.get("/", response_model=CarrierIntelligenceSummary)
def get_carrier_intelligence(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve transparent performance metrics and reliability ratings for logistics carriers."""
    return carrier_service.get_carrier_scores(
        db=db,
        org_id=current_user.organization_id,
    )
