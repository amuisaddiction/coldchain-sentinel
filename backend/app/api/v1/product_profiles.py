"""Product Profiles API router."""

from typing import List
from fastapi import APIRouter, Depends, status, Request, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_current_active_user,
    require_manager_or_admin,
    get_client_ip,
)
from app.models.user import User
from app.schemas.product_profile import (
    ProductProfileCreate,
    ProductProfileResponse,
)
from app.services import product_profile_service

router = APIRouter(prefix="/product-profiles", tags=["Product Profiles"])


@router.get("/", response_model=List[ProductProfileResponse])
def list_product_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List product profiles for caller's organization."""
    return product_profile_service.list_profiles(
        db=db,
        org_id=current_user.organization_id,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=ProductProfileResponse, status_code=status.HTTP_201_CREATED)
def create_product_profile(
    request: Request,
    payload: ProductProfileCreate,
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Create a new product profile with temperature thresholds."""
    client_ip = get_client_ip(request)
    return product_profile_service.create_profile(
        db=db,
        org_id=current_user.organization_id,
        name=payload.name,
        min_temp=payload.min_temperature_celsius,
        max_temp=payload.max_temperature_celsius,
        max_excursion_seconds=payload.max_excursion_duration_seconds,
        expected_sampling_seconds=payload.expected_sampling_interval_seconds,
        max_gap_seconds=payload.max_sampling_gap_seconds,
        user_id=current_user.id,
        client_ip=client_ip,
    )


@router.get("/{profile_id}", response_model=ProductProfileResponse)
def get_product_profile(
    profile_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve product profile details."""
    profile = product_profile_service.get_profile_by_id(
        db=db,
        org_id=current_user.organization_id,
        profile_id=profile_id,
    )
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product profile not found in your organization",
        )
    return profile
