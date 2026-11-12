"""Authentication and session management API router."""

import logging
import urllib.parse
from typing import Optional
import requests
from fastapi import APIRouter, Depends, status, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import generate_oauth_state, verify_oauth_state
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

logger = logging.getLogger(__name__)

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


@router.get("/google")
def google_login(
    return_url: Optional[str] = None,
):
    """Initiate Google OAuth2 authentication flow.
    
    Generates a tamper-proof signed state token, selects the environment-appropriate
    redirect URI (localhost in development, Render domain in production), and redirects
    the user to Google Accounts consent.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured on this server. GOOGLE_CLIENT_ID is missing.",
        )

    redirect_uri = settings.resolved_google_redirect_uri
    state = generate_oauth_state({"return_url": return_url} if return_url else None)

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get("/google/callback")
def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Handle Google OAuth2 callback.
    
    1. Validates the HMAC-signed state token to prevent CSRF.
    2. Exchanges the authorization code for Google access token.
    3. Fetches the verified user profile from Google.
    4. Auto-provisions or retrieves the local User in the database.
    5. Issues ColdChain Sentinel JWT tokens and redirects to the frontend callback handler.
    """
    frontend_base = settings.resolved_frontend_url

    if error:
        logger.warning("Google OAuth callback returned provider error: %s", error)
        return RedirectResponse(
            url=f"{frontend_base}/auth/callback?error={urllib.parse.quote(error)}",
            status_code=status.HTTP_302_FOUND,
        )

    if not code or not state:
        logger.warning("Google OAuth callback called without required code or state parameter")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required authorization code or state parameter",
        )

    is_valid, state_data = verify_oauth_state(state)
    if not is_valid:
        logger.warning("Google OAuth state validation failed (possible CSRF attempt or expired state)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state parameter (CSRF protection failed)",
        )

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth exchange failed: server missing credentials")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth credentials are not configured on the backend server",
        )

    redirect_uri = settings.resolved_google_redirect_uri
    client_ip = get_client_ip(request)

    try:
        # Step 1: Exchange code for Google access token
        token_resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )

        if not token_resp.ok:
            logger.error("Google token exchange failed: %s", token_resp.text)
            return RedirectResponse(
                url=f"{frontend_base}/auth/callback?error=token_exchange_failed",
                status_code=status.HTTP_302_FOUND,
            )

        token_data = token_resp.json()
        google_access_token = token_data.get("access_token")

        # Step 2: Fetch user profile
        userinfo_resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
            timeout=10,
        )

        if not userinfo_resp.ok:
            logger.error("Google userinfo request failed: %s", userinfo_resp.text)
            return RedirectResponse(
                url=f"{frontend_base}/auth/callback?error=userinfo_failed",
                status_code=status.HTTP_302_FOUND,
            )

        user_info = userinfo_resp.json()
        email = user_info.get("email")
        if not email or not user_info.get("email_verified", True):
            logger.warning("Google account email missing or unverified: %s", email)
            return RedirectResponse(
                url=f"{frontend_base}/auth/callback?error=unverified_email",
                status_code=status.HTTP_302_FOUND,
            )

        full_name = user_info.get("name") or email.split("@")[0]

        # Step 3: Find or provision user in DB
        user = auth_service.get_or_create_google_user(
            db=db,
            email=email,
            full_name=full_name,
            client_ip=client_ip,
        )

        # Step 4: Generate JWT token pair
        tokens = auth_service.generate_tokens_for_user(db=db, user=user, client_ip=client_ip)

        # Step 5: Redirect to frontend with tokens
        return_url = state_data.get("return_url") if state_data else None
        target = f"{frontend_base}/auth/callback?token={tokens.access_token}&refresh_token={tokens.refresh_token}"
        if return_url:
            target += f"&return_url={urllib.parse.quote(return_url)}"

        return RedirectResponse(url=target, status_code=status.HTTP_302_FOUND)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in Google OAuth callback: %s", exc)
        return RedirectResponse(
            url=f"{frontend_base}/auth/callback?error=server_error",
            status_code=status.HTTP_302_FOUND,
        )
