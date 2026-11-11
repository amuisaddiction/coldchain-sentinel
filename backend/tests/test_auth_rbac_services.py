"""Tests for authentication services, RBAC enforcement, tenant isolation, and Last-Admin invariant."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.database import Base
from app.models.enums import UserRole, OrganizationStatus
from app.models.user import User
from app.models.organization import Organization
from app.models.audit import AuditEvent
from app.services import (
    auth_service,
    user_service,
    organization_service,
)


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


def test_organization_onboarding_and_admin_creation(db_session):
    """Verify organization creation creates initial ADMIN user and logs audit event."""
    org, admin = organization_service.create_organization(
        db=db_session,
        name="PharmaCorp Bio",
        slug="pharmacorp",
        admin_email="admin@pharmacorp.com",
        admin_password="Password123!",
        admin_name="Dr. Alice Smith",
    )
    assert org.id is not None
    assert org.slug == "pharmacorp"
    assert org.status == OrganizationStatus.ACTIVE
    assert admin.organization_id == org.id
    assert admin.role == UserRole.ADMIN
    assert admin.email == "admin@pharmacorp.com"
    assert admin.is_active is True

    # Audit event verified
    audit = db_session.scalar(select(AuditEvent).where(AuditEvent.entity_id == org.id))
    assert audit is not None
    assert audit.action == "ORGANIZATION_ONBOARD"


def test_duplicate_organization_slug_and_email_rejection(db_session):
    """Verify duplicate org slug or user email is rejected with 409 Conflict."""
    organization_service.create_organization(
        db=db_session,
        name="PharmaCorp Bio",
        slug="pharmacorp",
        admin_email="admin@pharmacorp.com",
        admin_password="Password123!",
        admin_name="Dr. Alice Smith",
    )
    # Duplicate slug
    with pytest.raises(HTTPException) as exc1:
        organization_service.create_organization(
            db=db_session,
            name="PharmaCorp Other",
            slug="pharmacorp",
            admin_email="other@pharmacorp.com",
            admin_password="Password123!",
            admin_name="Bob",
        )
    assert exc1.value.status_code == 409

    # Duplicate email
    with pytest.raises(HTTPException) as exc2:
        organization_service.create_organization(
            db=db_session,
            name="Different Corp",
            slug="diffcorp",
            admin_email="admin@pharmacorp.com",
            admin_password="Password123!",
            admin_name="Bob",
        )
    assert exc2.value.status_code == 409


def test_login_success_and_failures(db_session):
    """Verify successful login, invalid credentials, deactivated user, and suspended org."""
    org, admin = organization_service.create_organization(
        db=db_session,
        name="BioLogistics",
        slug="biologistics",
        admin_email="lead@biologistics.com",
        admin_password="SecurePassword999!",
        admin_name="Lead Operator",
    )

    # 1. Success
    tokens = auth_service.login(db=db_session, email="lead@biologistics.com", password="SecurePassword999!")
    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "bearer"

    # 2. Invalid password -> 401
    with pytest.raises(HTTPException) as exc_bad_pwd:
        auth_service.login(db=db_session, email="lead@biologistics.com", password="WrongPassword!")
    assert exc_bad_pwd.value.status_code == 401

    # 3. Unknown email -> 401
    with pytest.raises(HTTPException) as exc_unknown:
        auth_service.login(db=db_session, email="unknown@biologistics.com", password="SecurePassword999!")
    assert exc_unknown.value.status_code == 401

    # 4. Deactivated user -> 403
    admin.is_active = False
    db_session.commit()
    with pytest.raises(HTTPException) as exc_inactive:
        auth_service.login(db=db_session, email="lead@biologistics.com", password="SecurePassword999!")
    assert exc_inactive.value.status_code == 403

    # Reactivate user
    admin.is_active = True
    db_session.commit()

    # 5. Suspended organization -> 403
    organization_service.update_organization_status(db=db_session, org_id=org.id, new_status=OrganizationStatus.SUSPENDED)
    with pytest.raises(HTTPException) as exc_suspended:
        auth_service.login(db=db_session, email="lead@biologistics.com", password="SecurePassword999!")
    assert exc_suspended.value.status_code == 403


def test_token_invalidation_on_password_change_and_logout(db_session):
    """Verify token_version increment invalidates prior sessions on password change and logout."""
    org, admin = organization_service.create_organization(
        db=db_session,
        name="CryoCare Inc",
        slug="cryocare",
        admin_email="admin@cryocare.com",
        admin_password="InitialPassword123!",
        admin_name="Admin",
    )
    initial_version = admin.token_version

    # Password change
    auth_service.change_password(
        db=db_session,
        user=admin,
        current_password="InitialPassword123!",
        new_password="NewSecurePassword456!",
    )
    assert admin.token_version == initial_version + 1

    # Logout
    auth_service.logout(db=db_session, user=admin)
    assert admin.token_version == initial_version + 2


def test_user_creation_and_tenant_isolation(db_session):
    """Verify users created within Org A cannot be seen or manipulated by Org B."""
    org_a, admin_a = organization_service.create_organization(
        db=db_session,
        name="Org Alpha",
        slug="org-alpha",
        admin_email="admin@alpha.com",
        admin_password="Password123!",
        admin_name="Admin Alpha",
    )
    org_b, admin_b = organization_service.create_organization(
        db=db_session,
        name="Org Beta",
        slug="org-beta",
        admin_email="admin@beta.com",
        admin_password="Password123!",
        admin_name="Admin Beta",
    )

    user_a = user_service.create_user(
        db=db_session,
        org_id=org_a.id,
        email="operator@alpha.com",
        password="Password123!",
        full_name="Operator Alpha",
        role=UserRole.OPERATOR,
    )

    # Org A sees user_a
    found_a = user_service.get_user_by_id(db=db_session, org_id=org_a.id, user_id=user_a.id)
    assert found_a is not None
    assert found_a.email == "operator@alpha.com"

    # Org B CANNOT see user_a
    found_b = user_service.get_user_by_id(db=db_session, org_id=org_b.id, user_id=user_a.id)
    assert found_b is None

    # Org B CANNOT update user_a role
    with pytest.raises(HTTPException) as exc:
        user_service.update_user_role(
            db=db_session,
            org_id=org_b.id,
            user_id=user_a.id,
            new_role=UserRole.MANAGER,
        )
    assert exc.value.status_code == 404


def test_last_admin_protection_invariant(db_session):
    """Verify that the sole active administrator cannot be demoted or deactivated."""
    org, admin = organization_service.create_organization(
        db=db_session,
        name="Secure Labs",
        slug="secure-labs",
        admin_email="sole-admin@securelabs.com",
        admin_password="Password123!",
        admin_name="Sole Admin",
    )

    # 1. Attempting to demote sole admin to OPERATOR must fail
    with pytest.raises(HTTPException) as exc_demote:
        user_service.update_user_role(
            db=db_session,
            org_id=org.id,
            user_id=admin.id,
            new_role=UserRole.OPERATOR,
        )
    assert exc_demote.value.status_code == 400
    assert "Cannot demote the last active administrator" in exc_demote.value.detail

    # 2. Attempting to deactivate sole admin must fail
    with pytest.raises(HTTPException) as exc_deactivate:
        user_service.update_user_status(
            db=db_session,
            org_id=org.id,
            user_id=admin.id,
            is_active=False,
        )
    assert exc_deactivate.value.status_code == 400
    assert "Cannot deactivate the last active administrator" in exc_deactivate.value.detail

    # 3. Create a second admin in the same org
    admin2 = user_service.create_user(
        db=db_session,
        org_id=org.id,
        email="second-admin@securelabs.com",
        password="Password123!",
        full_name="Second Admin",
        role=UserRole.ADMIN,
    )

    # 4. Now demoting the first admin succeeds because admin2 remains active
    demoted = user_service.update_user_role(
        db=db_session,
        org_id=org.id,
        user_id=admin.id,
        new_role=UserRole.MANAGER,
    )
    assert demoted.role == UserRole.MANAGER

    # 5. Demoting admin2 now fails because admin2 is the sole remaining active admin
    with pytest.raises(HTTPException) as exc_sole2:
        user_service.update_user_role(
            db=db_session,
            org_id=org.id,
            user_id=admin2.id,
            new_role=UserRole.OPERATOR,
        )
    assert exc_sole2.value.status_code == 400
