"""User schemas for creation, update, and display."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import UserRole


class UserCreate(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password, minimum 8 characters")
    full_name: str = Field(..., min_length=1, max_length=255, description="User full name")
    role: UserRole = Field(default=UserRole.OPERATOR, description="Assigned role")
    organization_id: Optional[str] = Field(None, description="Organization ID (for system admin creation)")


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)


class UserRoleUpdate(BaseModel):
    role: UserRole = Field(..., description="New role for the user")


class UserStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Active or deactivated status")


class UserResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
