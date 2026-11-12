"""Unit tests for Google OAuth2 authentication flow, environment-based redirect URI, and CSRF state security."""

import time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.config import Settings
from app.core.security import generate_oauth_state, verify_oauth_state
from app.models.organization import Organization
from app.models.user import User
from app.models.enums import OrganizationStatus, UserRole
from app.services import auth_service
from sqlalchemy.orm import Session


@pytest.fixture
def db_session():
    """Create an isolated in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_resolved_google_redirect_uri_environment_logic():
    """Verify callback URL is environment-aware: localhost in dev, Render in production."""
    # Development mode
    dev_settings = Settings(
        APP_ENV="development",
        GOOGLE_REDIRECT_URI="",
    )
    assert dev_settings.resolved_google_redirect_uri == "http://localhost:8000/api/auth/google/callback"

    # Production mode
    prod_settings = Settings(
        APP_ENV="production",
        GOOGLE_REDIRECT_URI="",
    )
    assert prod_settings.resolved_google_redirect_uri == "https://coldchain-sentinel-7ax3.onrender.com/api/auth/google/callback"

    # Explicit override takes priority in any environment
    custom_settings = Settings(
        APP_ENV="production",
        GOOGLE_REDIRECT_URI="https://custom.coldchain.io/api/auth/google/callback",
    )
    assert custom_settings.resolved_google_redirect_uri == "https://custom.coldchain.io/api/auth/google/callback"


def test_resolved_frontend_url_logic():
    """Verify frontend URL defaults to localhost in dev and Vercel in production."""
    dev_settings = Settings(APP_ENV="development", FRONTEND_URL="http://localhost:3000")
    assert dev_settings.resolved_frontend_url == "http://localhost:3000"

    prod_settings = Settings(APP_ENV="production", FRONTEND_URL="http://localhost:3000")
    assert prod_settings.resolved_frontend_url == "https://coldchain-sentinel.vercel.app"

    custom_prod = Settings(APP_ENV="production", FRONTEND_URL="https://app.coldchain.io")
    assert custom_prod.resolved_frontend_url == "https://app.coldchain.io"


def test_oauth_state_generation_and_tamper_detection():
    """Verify HMAC-SHA256 OAuth state token validates successfully and rejects tampering."""
    state = generate_oauth_state({"return_url": "/dashboard"})
    assert isinstance(state, str)
    assert ":" in state

    # Valid state passes
    is_valid, data = verify_oauth_state(state)
    assert is_valid is True
    assert data == {"return_url": "/dashboard"}

    # Tampered signature is rejected
    parts = state.split(":")
    tampered_sig = parts[:-1] + ["0" * 32]
    is_valid, _ = verify_oauth_state(":".join(tampered_sig))
    assert is_valid is False

    # Tampered content is rejected
    tampered_content = ["9999999999"] + parts[1:]
    is_valid, _ = verify_oauth_state(":".join(tampered_content))
    assert is_valid is False

    # Empty / malformed states rejected
    assert verify_oauth_state("")[0] is False
    assert verify_oauth_state("invalid")[0] is False


def test_oauth_state_expiration():
    """Verify expired state tokens (> 600s) are rejected."""
    # Artificially create an old timestamp (15 minutes ago)
    old_timestamp = int(time.time()) - 900
    from app.core.config import settings
    import hmac
    import hashlib

    content = f"{old_timestamp}:mocknonce"
    sig = hmac.new(settings.APP_SECRET_KEY.encode(), content.encode(), hashlib.sha256).hexdigest()[:32]
    old_state = f"{content}:{sig}"

    is_valid, _ = verify_oauth_state(old_state, max_age_seconds=600)
    assert is_valid is False


def test_get_or_create_google_user_provisioning(db_session: Session):
    """Verify auto-provisioning of Google users into default active organization."""
    import uuid
    org_id = str(uuid.uuid4())
    # Ensure active org exists
    org = Organization(
        id=org_id,
        name="OAuth Test Alliance",
        slug="oauth-test-alliance",
        status=OrganizationStatus.ACTIVE,
    )
    db_session.add(org)
    db_session.commit()

    # Provision user
    user = auth_service.get_or_create_google_user(
        db=db_session,
        email="operator.clara@coldchain-pharma.com",
        full_name="Clara Operator",
    )
    assert user.id is not None
    assert user.email == "operator.clara@coldchain-pharma.com"
    assert user.full_name == "Clara Operator"
    assert user.role == UserRole.OPERATOR
    assert user.is_active is True

    # Calling again returns the existing user without duplicate error
    user2 = auth_service.get_or_create_google_user(
        db=db_session,
        email="operator.clara@coldchain-pharma.com",
        full_name="Clara Updated",
    )
    assert user2.id == user.id

    # Token generation works
    tokens = auth_service.generate_tokens_for_user(db_session, user)
    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "bearer"
