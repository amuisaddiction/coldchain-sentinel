"""Shipment schemas for creation, status updating, and display."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import ShipmentStatus


class ShipmentCreate(BaseModel):
    product_profile_id: str = Field(..., description="UUID of the product profile rules")
    tracking_number: str = Field(..., min_length=3, max_length=100, description="Unique carrier tracking code")
    origin: str = Field(..., min_length=2, max_length=255, description="Shipment origin facility / location")
    destination: str = Field(..., min_length=2, max_length=255, description="Destination facility / clinical site")


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus = Field(..., description="Target status transition")


class ShipmentResponse(BaseModel):
    id: str
    organization_id: str
    product_profile_id: str
    created_by: Optional[str]
    tracking_number: str
    status: ShipmentStatus
    origin: str
    destination: str
    dispatched_at: Optional[datetime]
    delivered_at: Optional[datetime]
    rule_profile_version: int
    rule_min_temperature_celsius: Decimal
    rule_max_temperature_celsius: Decimal
    rule_max_excursion_duration_seconds: int
    rule_expected_sampling_interval_seconds: int
    rule_max_sampling_gap_seconds: int
    rule_source_reference: str
    rule_snapshot_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
