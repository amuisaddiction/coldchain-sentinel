"""Custody transfer schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import CustodyEventType


class CustodyEventCreate(BaseModel):
    event_type: CustodyEventType = Field(..., description="Stage of custody transfer")
    carrier_name: str = Field(..., min_length=2, max_length=255, description="Operating carrier name")
    custodian_name: str = Field(..., min_length=2, max_length=255, description="Sign-off custodian / officer name")
    location: str = Field(..., min_length=2, max_length=255, description="Physical location / checkpoint")
    recorded_at: Optional[datetime] = Field(None, description="Actual physical transfer timestamp")
    evidence_file_id: Optional[str] = Field(None, description="Optional sign-off sheet or manifest evidence UUID")
    notes: Optional[str] = Field(None, description="Operational notes or observations")


class CustodyEventResponse(BaseModel):
    id: str
    shipment_id: str
    organization_id: str
    evidence_file_id: Optional[str]
    actor_user_id: Optional[str]
    event_type: CustodyEventType
    carrier_name: str
    custodian_name: str
    location: str
    notes: Optional[str]
    recorded_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
