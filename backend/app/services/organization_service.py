"""Organization service for multi-tenant isolation, onboarding, and lifecycle management."""

import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.organization import Organization
from app.models.user import User
from app.models.enums import OrganizationStatus, UserRole
from app.core.security import hash_password
from app.core.regex import validate_email_format
from app.services.audit_service import log_audit_event


def get_organization_by_id(db: Session, org_id: str) -> Optional[Organization]:
    """Retrieve organization by its UUID."""
    return db.scalar(select(Organization).where(Organization.id == org_id))


def list_organizations(db: Session, skip: int = 0, limit: int = 50) -> List[Organization]:
    """List organizations with pagination."""
    return list(
        db.scalars(
            select(Organization)
            .offset(skip)
            .limit(limit)
            .order_by(Organization.created_at.desc())
        ).all()
    )


def create_organization(
    db: Session,
    name: str,
    slug: str,
    admin_email: str,
    admin_password: str,
    admin_name: str,
    client_ip: Optional[str] = None,
) -> Tuple[Organization, User]:
    """Atomically onboard a new organization along with its initial administrator."""
    # Validate slug uniqueness
    existing_org = db.scalar(select(Organization).where(Organization.slug == slug.lower().strip()))
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization slug '{slug}' is already taken",
        )

    # Validate admin email
    is_valid, norm_email = validate_email_format(admin_email)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=norm_email,
        )

    existing_user = db.scalar(select(User).where(User.email == norm_email.lower()))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists",
        )

    org = Organization(
        id=str(uuid.uuid4()),
        name=name.strip(),
        slug=slug.lower().strip(),
        status=OrganizationStatus.ACTIVE,
        auth_version=1,
    )
    db.add(org)
    db.flush()

    admin_user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=norm_email.lower(),
        hashed_password=hash_password(admin_password),
        full_name=admin_name.strip(),
        role=UserRole.ADMIN,
        is_active=True,
        token_version=1,
    )
    db.add(admin_user)
    db.flush()

    log_audit_event(
        db=db,
        organization_id=org.id,
        user_id=admin_user.id,
        entity_type="ORGANIZATION",
        entity_id=org.id,
        action="ORGANIZATION_ONBOARD",
        payload_after={"slug": org.slug, "admin_email": admin_user.email},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(org)
    db.refresh(admin_user)

    return org, admin_user


def update_organization_status(
    db: Session,
    org_id: str,
    new_status: OrganizationStatus,
    actor_user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> Organization:
    """Update organization status and increment auth_version to invalidate tokens."""
    org = get_organization_by_id(db, org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    old_status = org.status
    org.status = new_status
    org.auth_version += 1  # Invalidate all existing tokens across the organization

    log_audit_event(
        db=db,
        organization_id=org.id,
        user_id=actor_user_id,
        entity_type="ORGANIZATION",
        entity_id=org.id,
        action="ORGANIZATION_STATUS_UPDATE",
        payload_before={"status": old_status.value if hasattr(old_status, "value") else str(old_status)},
        payload_after={"status": new_status.value if hasattr(new_status, "value") else str(new_status)},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(org)
    return org
