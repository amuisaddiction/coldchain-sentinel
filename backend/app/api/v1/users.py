"""User management and role administration API router."""

from typing import List
from fastapi import APIRouter, Depends, status, Request, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_current_active_user,
    require_admin,
    require_manager_or_admin,
    get_client_ip,
)
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserRoleUpdate,
    UserStatusUpdate,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """List users within the caller's tenant organization."""
    return user_service.list_users(
        db=db,
        org_id=current_user.organization_id,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: Request,
    payload: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new user within the administrator's organization."""
    client_ip = get_client_ip(request)
    return user_service.create_user(
        db=db,
        org_id=current_user.organization_id,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        creator_user_id=current_user.id,
        client_ip=client_ip,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve user details within caller's organization."""
    user = user_service.get_user_by_id(
        db=db,
        org_id=current_user.organization_id,
        user_id=user_id,
    )
    if not user:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in organization",
        )
    return user


@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    request: Request,
    user_id: str,
    payload: UserRoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update user role, enforcing Last-Admin protection."""
    client_ip = get_client_ip(request)
    return user_service.update_user_role(
        db=db,
        org_id=current_user.organization_id,
        user_id=user_id,
        new_role=payload.role,
        actor_user_id=current_user.id,
        client_ip=client_ip,
    )


@router.put("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    request: Request,
    user_id: str,
    payload: UserStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activate or deactivate user, enforcing Last-Admin protection."""
    client_ip = get_client_ip(request)
    return user_service.update_user_status(
        db=db,
        org_id=current_user.organization_id,
        user_id=user_id,
        is_active=payload.is_active,
        actor_user_id=current_user.id,
        client_ip=client_ip,
    )
