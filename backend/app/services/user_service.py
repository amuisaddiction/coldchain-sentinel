"""User service providing user CRUD, role management, and Last-Admin protection."""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.organization import Organization
from app.models.enums import UserRole
from app.core.security import hash_password
from app.core.regex import validate_email_format
from app.services.audit_service import log_audit_event


def get_user_by_id(db: Session, org_id: str, user_id: str) -> Optional[User]:
    """Retrieve user strictly scoped to the tenant organization."""
    return db.scalar(
        select(User).where(User.organization_id == org_id, User.id == user_id)
    )


def list_users(db: Session, org_id: str, skip: int = 0, limit: int = 50) -> List[User]:
    """List users strictly within tenant organization."""
    return list(
        db.scalars(
            select(User)
            .where(User.organization_id == org_id)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        ).all()
    )


def create_user(
    db: Session,
    org_id: str,
    email: str,
    password: str,
    full_name: str,
    role: UserRole = UserRole.OPERATOR,
    creator_user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> User:
    """Create a new user within an organization with strict email and tenant validation."""
    is_valid, norm_email = validate_email_format(email)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=norm_email,
        )

    # Check for existing email globally
    existing = db.scalar(select(User).where(User.email == norm_email.lower()))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists",
        )

    org = db.scalar(select(Organization).where(Organization.id == org_id))
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target organization not found",
        )

    user = User(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        email=norm_email.lower(),
        hashed_password=hash_password(password),
        full_name=full_name.strip(),
        role=role,
        is_active=True,
        token_version=1,
    )
    db.add(user)
    db.flush()

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=creator_user_id,
        entity_type="USER",
        entity_id=user.id,
        action="USER_CREATE",
        payload_after={"email": user.email, "role": user.role.value if hasattr(user.role, "value") else str(user.role)},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(user)
    return user


def update_user_role(
    db: Session,
    org_id: str,
    user_id: str,
    new_role: UserRole,
    actor_user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> User:
    """Update user role with strict Last-Admin invariant protection."""
    user = get_user_by_id(db, org_id, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this organization",
        )

    old_role = user.role
    if old_role == UserRole.ADMIN and new_role != UserRole.ADMIN:
        # Check remaining active ADMINs in this organization
        active_admins_count = db.scalar(
            select(func.count(User.id)).where(
                User.organization_id == org_id,
                User.role == UserRole.ADMIN,
                User.is_active == True,
                User.id != user_id,
            )
        )
        if not active_admins_count or active_admins_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last active administrator of an organization",
            )

    user.role = new_role
    user.token_version += 1  # Invalidate prior sessions to apply new role

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=actor_user_id,
        entity_type="USER",
        entity_id=user.id,
        action="USER_ROLE_UPDATE",
        payload_before={"role": old_role.value if hasattr(old_role, "value") else str(old_role)},
        payload_after={"role": new_role.value if hasattr(new_role, "value") else str(new_role)},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(user)
    return user


def update_user_status(
    db: Session,
    org_id: str,
    user_id: str,
    is_active: bool,
    actor_user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> User:
    """Activate or deactivate user with strict Last-Admin invariant protection."""
    user = get_user_by_id(db, org_id, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this organization",
        )

    if user.role == UserRole.ADMIN and not is_active and user.is_active:
        active_admins_count = db.scalar(
            select(func.count(User.id)).where(
                User.organization_id == org_id,
                User.role == UserRole.ADMIN,
                User.is_active == True,
                User.id != user_id,
            )
        )
        if not active_admins_count or active_admins_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last active administrator of an organization",
            )

    old_status = user.is_active
    user.is_active = is_active
    user.token_version += 1  # Invalidate prior sessions

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=actor_user_id,
        entity_type="USER",
        entity_id=user.id,
        action="USER_STATUS_UPDATE",
        payload_before={"is_active": old_status},
        payload_after={"is_active": is_active},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(user)
    return user
