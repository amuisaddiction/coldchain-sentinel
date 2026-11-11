"""Carrier intelligence schemas."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class CarrierScoreResponse(BaseModel):
    carrier_name: str
    total_shipments: int
    compliant_shipments: int
    excursion_shipments: int
    compliance_rate_percent: float
    reliability_score: float
    sample_size_warning: bool
    sample_size_note: str

    model_config = ConfigDict(from_attributes=True)


class CarrierIntelligenceSummary(BaseModel):
    total_carriers_tracked: int
    carriers: List[CarrierScoreResponse]
