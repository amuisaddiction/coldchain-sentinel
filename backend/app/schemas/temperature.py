"""Temperature reading and summary schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import TemperatureSeverity


class TemperatureReadingCreate(BaseModel):
    sensor_id: str = Field(default="PRIMARY", max_length=100)
    recorded_at: datetime = Field(...)
    temperature_celsius: Decimal = Field(...)
    sequence_number: Optional[int] = Field(default=None, ge=0)


class TemperatureReadingResponse(BaseModel):
    id: str
    shipment_id: str
    evidence_file_id: str
    row_number: int
    sensor_id: str
    recorded_at: datetime
    temperature_celsius: Decimal
    severity: TemperatureSeverity
    sequence_number: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TemperatureSummaryResponse(BaseModel):
    shipment_id: str
    total_readings: int
    min_temperature: Optional[Decimal]
    max_temperature: Optional[Decimal]
    rule_min_temperature: Decimal
    rule_max_temperature: Decimal
    total_excursion_seconds: int
    allowed_excursion_seconds: int
    is_compliant: bool
    excursions_count: int
