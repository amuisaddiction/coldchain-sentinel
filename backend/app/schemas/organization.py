"""Organization schemas for creation, update, and display."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import OrganizationStatus


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Organization display name")
    slug: str = Field(..., min_length=2, max_length=100, description="Unique organization slug identifier")


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)


class OrganizationStatusUpdate(BaseModel):
    status: OrganizationStatus = Field(..., description="Organization operational status")


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    status: OrganizationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
