"""Authentication service handling login, refresh, password rotation, and token invalidation."""

import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.models.organization import Organization
from app.models.enums import OrganizationStatus
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_and_verify_token,
    InvalidTokenError,
)
from app.core.config import settings
from app.core.regex import validate_email_format
from app.schemas.auth import TokenResponse
from app.services.audit_service import log_audit_event

logger = logging.getLogger(__name__)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password, ensuring tenant is active."""
    is_valid, norm_email = validate_email_format(email)
    if not is_valid:
        return None

    user = db.scalar(select(User).where(User.email == norm_email.lower()))
    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def login(db: Session, email: str, password: str, client_ip: Optional[str] = None) -> TokenResponse:
    """Validate credentials, ensure active user & active org, then generate token pair."""
    user = authenticate_user(db, email, password)
    if not user:
        logger.warning("Failed login attempt for email: %s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning("Login rejected for deactivated user: %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    org = db.scalar(select(Organization).where(Organization.id == user.organization_id))
    if not org or org.status != OrganizationStatus.ACTIVE:
        logger.warning("Login rejected for user in suspended org: %s", user.organization_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive or suspended",
        )

    access_token = create_access_token(
        user_id=user.id,
        org_id=user.organization_id,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        token_version=user.token_version,
        auth_version=org.auth_version,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        org_id=user.organization_id,
        token_version=user.token_version,
        auth_version=org.auth_version,
    )

    log_audit_event(
        db=db,
        organization_id=user.organization_id,
        user_id=user.id,
        entity_type="AUTH",
        entity_id=user.id,
        action="LOGIN_SUCCESS",
        ip_address=client_ip,
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def refresh(db: Session, refresh_token_str: str) -> TokenResponse:
    """Validate refresh token and issue new token pair."""
    try:
        claims = decode_and_verify_token(refresh_token_str, expected_type="refresh")
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = claims["sub"]
    user = db.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    if user.token_version != claims.get("token_version"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    org = db.scalar(select(Organization).where(Organization.id == user.organization_id))
    if not org or org.status != OrganizationStatus.ACTIVE or org.auth_version != claims.get("auth_version"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive or suspended",
        )

    access_token = create_access_token(
        user_id=user.id,
        org_id=user.organization_id,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        token_version=user.token_version,
        auth_version=org.auth_version,
    )
    new_refresh_token = create_refresh_token(
        user_id=user.id,
        org_id=user.organization_id,
        token_version=user.token_version,
        auth_version=org.auth_version,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
    client_ip: Optional[str] = None,
) -> bool:
    """Change user password, increment token_version to invalidate prior tokens, and audit."""
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long",
        )

    user.hashed_password = hash_password(new_password)
    user.token_version += 1  # Invalidate all existing sessions

    log_audit_event(
        db=db,
        organization_id=user.organization_id,
        user_id=user.id,
        entity_type="USER",
        entity_id=user.id,
        action="PASSWORD_CHANGE",
        ip_address=client_ip,
    )
    db.commit()
    return True


def logout(db: Session, user: User, client_ip: Optional[str] = None) -> bool:
    """Logout user by incrementing token_version to invalidate tokens immediately."""
    user.token_version += 1
    log_audit_event(
        db=db,
        organization_id=user.organization_id,
        user_id=user.id,
        entity_type="AUTH",
        entity_id=user.id,
        action="LOGOUT",
        ip_address=client_ip,
    )
    db.commit()
    return True


def get_or_create_google_user(
    db: Session,
    email: str,
    full_name: str,
    client_ip: Optional[str] = None,
) -> User:
    """Find existing user by email or provision new user under the default active organization."""
    import uuid
    from app.models.enums import UserRole

    norm_email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == norm_email))
    if user:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )
        org = db.scalar(select(Organization).where(Organization.id == user.organization_id))
        if not org or org.status != OrganizationStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization is inactive or suspended",
            )
        return user

    # Auto-provision user under the primary active organization
    org = db.scalar(select(Organization).where(Organization.status == OrganizationStatus.ACTIVE).order_by(Organization.created_at))
    if not org:
        org = Organization(
            id=str(uuid.uuid4()),
            name="ColdChain Logistics Alliance",
            slug="coldchain-alliance",
            status=OrganizationStatus.ACTIVE,
        )
        db.add(org)
        db.flush()

    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=norm_email,
        hashed_password=hash_password(uuid.uuid4().hex),  # Unguessable random hash for OAuth user
        full_name=full_name or "Google User",
        role=UserRole.OPERATOR,
        is_active=True,
    )
    db.add(user)
    log_audit_event(
        db=db,
        organization_id=org.id,
        user_id=user.id,
        entity_type="USER",
        entity_id=user.id,
        action="GOOGLE_OAUTH_PROVISION",
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(user)
    return user


def generate_tokens_for_user(db: Session, user: User, client_ip: Optional[str] = None) -> TokenResponse:
    """Generate PyJWT access & refresh tokens for an authenticated user."""
    org = db.scalar(select(Organization).where(Organization.id == user.organization_id))
    auth_version = org.auth_version if org else 1

    access_token = create_access_token(
        user_id=user.id,
        org_id=user.organization_id,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        token_version=user.token_version,
        auth_version=auth_version,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        org_id=user.organization_id,
        token_version=user.token_version,
        auth_version=auth_version,
    )

    log_audit_event(
        db=db,
        organization_id=user.organization_id,
        user_id=user.id,
        entity_type="AUTH",
        entity_id=user.id,
        action="LOGIN_GOOGLE_SUCCESS",
        ip_address=client_ip,
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
