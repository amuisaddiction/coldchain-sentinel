"""Investigation and incident report schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import InvestigationStatus, InvestigationPriority


class InvestigationCreate(BaseModel):
    shipment_id: str = Field(..., description="UUID of the shipment under inquiry")
    priority: InvestigationPriority = Field(default=InvestigationPriority.MEDIUM)
    assigned_to: Optional[str] = Field(None, description="Assigned investigator user UUID")
    findings: Optional[str] = Field(None, description="Initial incident observations")


class InvestigationUpdate(BaseModel):
    status: Optional[InvestigationStatus] = None
    priority: Optional[InvestigationPriority] = None
    assigned_to: Optional[str] = None
    findings: Optional[str] = None
    resolution_summary: Optional[str] = None


class InvestigationResponse(BaseModel):
    id: str
    shipment_id: str
    organization_id: str
    assigned_to: Optional[str]
    status: InvestigationStatus
    priority: InvestigationPriority
    findings: Optional[str]
    resolution_summary: Optional[str]
    opened_at: datetime
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationReportResponse(BaseModel):
    investigation_id: str
    shipment_id: str
    organization_id: str
    tracking_number: str
    status: InvestigationStatus
    priority: InvestigationPriority
    findings: Optional[str]
    resolution_summary: Optional[str]
    shipment_details: Dict[str, Any]
    temperature_summary: Dict[str, Any]
    evidence_artifacts: List[Dict[str, Any]]
    verification_decisions: List[Dict[str, Any]]
    generated_at: datetime
