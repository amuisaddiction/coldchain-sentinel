"""Authentication and session management API router."""

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_client_ip
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    PasswordChangeRequest,
    UserProfileResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password to receive JWT access and refresh tokens."""
    client_ip = get_client_ip(request)
    return auth_service.login(db=db, email=payload.email, password=payload.password, client_ip=client_ip)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a newly issued access token and refresh token."""
    return auth_service.refresh(db=db, refresh_token_str=payload.refresh_token)


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve identity, role, and organization information for the authenticated user."""
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        organization_id=current_user.organization_id,
        organization_name=current_user.organization.name if current_user.organization else "",
        organization_status=current_user.organization.status if current_user.organization else "ACTIVE",
        is_active=current_user.is_active,
    )


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    request: Request,
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change password and revoke all existing session tokens."""
    client_ip = get_client_ip(request)
    auth_service.change_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        client_ip=client_ip,
    )
    return {"message": "Password changed successfully. All previous sessions have been invalidated."}


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Log out and revoke all active tokens for the user."""
    client_ip = get_client_ip(request)
    auth_service.logout(db=db, user=current_user, client_ip=client_ip)
    return {"message": "Logged out successfully."}
