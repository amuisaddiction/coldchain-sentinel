"""Sentinel Challenge schemas."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ChallengeScenarioResponse(BaseModel):
    scenario_id: str
    title: str
    description: str
    expected_outcome: str
    shipment_id: Optional[str]
    tracking_number: str
    status: str
    verification_decision: Optional[str]
    payment_status: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ChallengeResetResponse(BaseModel):
    message: str
    scenarios: List[ChallengeScenarioResponse]
