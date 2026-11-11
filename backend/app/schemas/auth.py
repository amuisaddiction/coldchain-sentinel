"""Authentication and token schemas."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import UserRole, OrganizationStatus


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User plaintext password")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password, minimum 8 characters")


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    organization_id: str
    organization_name: str
    organization_status: OrganizationStatus
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
