"""Verification decision schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import DecisionType


class VerificationDecisionResponse(BaseModel):
    id: str
    shipment_id: str
    organization_id: str
    decision: DecisionType
    confidence_score: Decimal
    evidence_hash_snapshot: str
    temperature_rule_passed: bool
    custody_chain_passed: bool
    sampling_frequency_passed: bool
    total_excursion_seconds: int
    max_temperature_detected: Optional[Decimal]
    min_temperature_detected: Optional[Decimal]
    reasoning_summary: str
    decided_by: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
