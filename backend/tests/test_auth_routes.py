"""Integration tests for authentication, user management, and organization API routes."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.core.database import Base, get_db
from app.main import app
from app.models.enums import UserRole, OrganizationStatus
from app.services import organization_service, user_service


@pytest.fixture
def client_and_db():
    """Setup an in-memory SQLite database and test client with overridden get_db dependency."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Seed an organization and admin
    org, admin = organization_service.create_organization(
        db=session,
        name="Global Pharma Test",
        slug="global-pharma",
        admin_email="admin@globalpharma.com",
        admin_password="Password123!",
        admin_name="Global Admin",
    )

    operator = user_service.create_user(
        db=session,
        org_id=org.id,
        email="operator@globalpharma.com",
        password="Password123!",
        full_name="Global Operator",
        role=UserRole.OPERATOR,
    )

    yield {
        "db": session,
        "org": org,
        "admin": admin,
        "operator": operator,
    }

    app.dependency_overrides.clear()
    session.close()


def test_api_login_and_me(client_and_db):
    """Verify POST /api/auth/login and GET /api/auth/me workflow."""
    db = client_and_db["db"]
    org = client_and_db["org"]

    # Call login service directly or via route function
    from app.api.v1.auth import login, get_current_user_profile
    from app.schemas.auth import LoginRequest

    dummy_request = Request({"type": "http", "client": ("127.0.0.1", 12345), "headers": []})
    login_resp = login(
        request=dummy_request,
        payload=LoginRequest(email="admin@globalpharma.com", password="Password123!"),
        db=db,
    )
    assert login_resp.access_token is not None
    assert login_resp.refresh_token is not None

    # Call /me endpoint with admin
    profile = get_current_user_profile(
        current_user=client_and_db["admin"],
        db=db,
    )
    assert profile.email == "admin@globalpharma.com"
    assert profile.role == UserRole.ADMIN
    assert profile.organization_id == org.id


def test_api_user_creation_and_role_management(client_and_db):
    """Verify user creation, listing, role update, and status update."""
    db = client_and_db["db"]
    org = client_and_db["org"]
    admin = client_and_db["admin"]
    dummy_request = Request({"type": "http", "client": ("127.0.0.1", 12345), "headers": []})

    from app.api.v1.users import create_user, list_users, update_user_role, update_user_status
    from app.schemas.user import UserCreate, UserRoleUpdate, UserStatusUpdate

    # Create new manager
    new_user = create_user(
        request=dummy_request,
        payload=UserCreate(
            email="manager@globalpharma.com",
            password="SecurePassword123!",
            full_name="Site Manager",
            role=UserRole.MANAGER,
        ),
        current_user=admin,
        db=db,
    )
    assert new_user.email == "manager@globalpharma.com"
    assert new_user.role == UserRole.MANAGER

    # List users
    users_list = list_users(
        skip=0,
        limit=50,
        current_user=admin,
        db=db,
    )
    emails = [u.email for u in users_list]
    assert "admin@globalpharma.com" in emails
    assert "operator@globalpharma.com" in emails
    assert "manager@globalpharma.com" in emails

    # Update manager to AUDITOR
    updated_role_user = update_user_role(
        request=dummy_request,
        user_id=new_user.id,
        payload=UserRoleUpdate(role=UserRole.AUDITOR),
        current_user=admin,
        db=db,
    )
    assert updated_role_user.role == UserRole.AUDITOR

    # Deactivate user
    deactivated_user = update_user_status(
        request=dummy_request,
        user_id=new_user.id,
        payload=UserStatusUpdate(is_active=False),
        current_user=admin,
        db=db,
    )
    assert deactivated_user.is_active is False
