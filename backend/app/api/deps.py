"""Authentication, authorization, tenant isolation, and proxy dependencies."""

import logging
from typing import List, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_and_verify_token, InvalidTokenError
from app.models.user import User
from app.models.organization import Organization
from app.models.enums import UserRole, OrganizationStatus

logger = logging.getLogger(__name__)

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP, inspecting X-Forwarded-For if client peer is trusted."""
    client_host = request.client.host if request.client else None
    xff = request.headers.get("X-Forwarded-For")
    if xff and client_host in ("127.0.0.1", "::1", "localhost"):
        # Take the leftmost untrusted IP from the comma-separated chain
        parts = [p.strip() for p in xff.split(",")]
        return parts[0] if parts else client_host
    return client_host


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(reusable_oauth2),
    db: Session = Depends(get_db),
) -> User:
    """Validate Bearer access token and resolve authenticated user with active tenant isolation."""
    if not token:
        # Check standard Authorization header fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = decode_and_verify_token(token, expected_type="access")
    except InvalidTokenError as exc:
        logger.warning("Token verification failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = claims["sub"]
    org_id = claims["org_id"]
    token_version = claims.get("token_version")
    auth_version = claims.get("auth_version")

    user = db.scalar(
        select(User).where(User.id == user_id, User.organization_id == org_id)
    )
    if not user:
        logger.warning("Principal not found for token sub: %s in org: %s", user_id, org_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning("Deactivated user attempted request: %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    if user.token_version != token_version:
        logger.warning("Revoked token version presented by user: %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    org = db.scalar(select(Organization).where(Organization.id == org_id))
    if not org or org.status != OrganizationStatus.ACTIVE:
        logger.warning("User in suspended organization attempted access: %s", org_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive or suspended",
        )

    if org.auth_version != auth_version:
        logger.warning("Outdated organization auth version in token for org: %s", org_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_roles(allowed_roles: List[UserRole]):
    """Factory creating an authorization dependency restricting endpoints by user roles."""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        allowed_vals = [r.value if hasattr(r, "value") else str(r) for r in allowed_roles]
        if user_role_val not in allowed_vals:
            logger.warning(
                "Role authorization failure: user %s (role %s) attempted action requiring %s",
                current_user.id,
                user_role_val,
                allowed_vals,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for current role",
            )
        return current_user

    return role_checker


require_admin = require_roles([UserRole.ADMIN])
require_manager_or_admin = require_roles([UserRole.ADMIN, UserRole.MANAGER])
require_operator_or_above = require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR])
require_auditor_or_above = require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.AUDITOR, UserRole.QUALITY_ASSURANCE])
