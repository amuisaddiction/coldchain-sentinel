"""Sentinel Challenge demonstration API router."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_manager_or_admin
from app.models.user import User
from app.schemas.challenge import (
    ChallengeScenarioResponse,
    ChallengeResetResponse,
)
from app.services import challenge_service

router = APIRouter(prefix="/challenge", tags=["Sentinel Challenge"])


@router.get("/scenarios", response_model=List[ChallengeScenarioResponse])
def get_challenge_scenarios(
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Retrieve the 4 reproducible Sentinel Challenge evaluation scenarios."""
    return challenge_service.reset_challenge(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
    )


@router.post("/reset", response_model=ChallengeResetResponse)
def reset_challenge_environment(
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """One-click deterministic reset restoring all 4 demonstration scenarios."""
    scenarios = challenge_service.reset_challenge(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return ChallengeResetResponse(
        message="Sentinel Challenge scenarios reset to clean deterministic initial state.",
        scenarios=scenarios,
    )
