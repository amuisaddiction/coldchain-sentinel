"""Organization onboarding and management API router."""

from fastapi import APIRouter, Depends, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_current_active_user,
    require_admin,
    get_client_ip,
)
from app.models.user import User
from app.schemas.organization import (
    OrganizationResponse,
    OrganizationStatusUpdate,
)
from app.schemas.user import UserResponse
from app.services import organization_service

router = APIRouter(prefix="/organizations", tags=["Organizations"])


class OrganizationOnboardRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    admin_email: str
    admin_password: str = Field(..., min_length=8)
    admin_name: str = Field(..., min_length=1)


class OrganizationOnboardResponse(BaseModel):
    organization: OrganizationResponse
    admin_user: UserResponse


@router.post("/onboard", response_model=OrganizationOnboardResponse, status_code=status.HTTP_201_CREATED)
def onboard_organization(
    request: Request,
    payload: OrganizationOnboardRequest,
    db: Session = Depends(get_db),
):
    """Onboard a new organization and create its initial administrator account."""
    client_ip = get_client_ip(request)
    org, admin = organization_service.create_organization(
        db=db,
        name=payload.name,
        slug=payload.slug,
        admin_email=payload.admin_email,
        admin_password=payload.admin_password,
        admin_name=payload.admin_name,
        client_ip=client_ip,
    )
    return {
        "organization": org,
        "admin_user": admin,
    }


@router.get("/current", response_model=OrganizationResponse)
def get_current_organization(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve the caller's organization details."""
    org = organization_service.get_organization_by_id(
        db=db,
        org_id=current_user.organization_id,
    )
    if not org:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    return org


@router.put("/{org_id}/status", response_model=OrganizationResponse)
def update_organization_status(
    request: Request,
    org_id: str,
    payload: OrganizationStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update organization operational status and revoke all tokens if suspended."""
    # Enforce tenant isolation: user can only modify their own organization
    if current_user.organization_id != org_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another organization",
        )

    client_ip = get_client_ip(request)
    return organization_service.update_organization_status(
        db=db,
        org_id=org_id,
        new_status=payload.status,
        actor_user_id=current_user.id,
        client_ip=client_ip,
    )
