"""Product profile service for temperature rules and versioning."""

import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.product_profile import ProductProfile
from app.services.audit_service import log_audit_event


def get_profile_by_id(db: Session, org_id: str, profile_id: str) -> Optional[ProductProfile]:
    """Retrieve product profile strictly scoped to organization."""
    return db.scalar(
        select(ProductProfile).where(
            ProductProfile.organization_id == org_id,
            ProductProfile.id == profile_id,
        )
    )


def list_profiles(db: Session, org_id: str, skip: int = 0, limit: int = 50) -> List[ProductProfile]:
    """List product profiles for organization."""
    return list(
        db.scalars(
            select(ProductProfile)
            .where(ProductProfile.organization_id == org_id)
            .offset(skip)
            .limit(limit)
            .order_by(ProductProfile.created_at.desc())
        ).all()
    )


def create_profile(
    db: Session,
    org_id: str,
    name: str,
    min_temp: Decimal,
    max_temp: Decimal,
    max_excursion_seconds: int = 0,
    expected_sampling_seconds: int = 300,
    max_gap_seconds: int = 600,
    user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> ProductProfile:
    """Create a new product profile rule set."""
    if min_temp >= max_temp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum temperature must be strictly less than maximum temperature",
        )
    if expected_sampling_seconds <= 0 or max_gap_seconds <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sampling interval and max gap must be positive",
        )
    if max_gap_seconds < expected_sampling_seconds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum gap cannot be less than expected sampling interval",
        )

    profile = ProductProfile(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        name=name.strip(),
        version=1,
        min_temperature_celsius=min_temp,
        max_temperature_celsius=max_temp,
        max_excursion_duration_seconds=max_excursion_seconds,
        expected_sampling_interval_seconds=expected_sampling_seconds,
        max_sampling_gap_seconds=max_gap_seconds,
        is_active=True,
        is_locked=False,
    )
    db.add(profile)
    db.flush()

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=user_id,
        entity_type="PRODUCT_PROFILE",
        entity_id=profile.id,
        action="PROFILE_CREATE",
        payload_after={"name": profile.name, "min": str(min_temp), "max": str(max_temp)},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(profile)
    return profile
