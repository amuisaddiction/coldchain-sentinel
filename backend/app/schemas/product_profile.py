"""ProductProfile schemas for creation, update, and display."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductProfileCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Product / vaccine profile name")
    min_temperature_celsius: Decimal = Field(..., description="Minimum allowable temperature (°C)")
    max_temperature_celsius: Decimal = Field(..., description="Maximum allowable temperature (°C)")
    max_excursion_duration_seconds: int = Field(default=0, ge=0, description="Allowed excursion budget in seconds")
    expected_sampling_interval_seconds: int = Field(default=300, gt=0, description="Expected interval between readings")
    max_sampling_gap_seconds: int = Field(default=600, gt=0, description="Maximum tolerated gap between readings")


class ProductProfileResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    version: int
    min_temperature_celsius: Decimal
    max_temperature_celsius: Decimal
    max_excursion_duration_seconds: int
    expected_sampling_interval_seconds: int
    max_sampling_gap_seconds: int
    is_active: bool
    is_locked: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
