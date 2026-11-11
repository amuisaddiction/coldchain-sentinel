"""Pydantic schemas for AI Contract Intelligence and Settlement Decision Engine."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ContractClause(BaseModel):
    clause_id: str
    category: str = Field(..., description="TEMPERATURE, DELIVERY_DEADLINE, CUSTODY, QUALITY, PAYMENT, PENALTY")
    title: str
    text_excerpt: str
    requirement_summary: str
    source_document: str
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    is_verified_by_reviewer: bool = False


class PharmaContract(BaseModel):
    contract_id: str
    title: str
    parties: List[str]
    effective_date: str
    medicine_name: str
    permitted_min_temp_celsius: Decimal
    permitted_max_temp_celsius: Decimal
    max_excursion_duration_seconds: int
    delivery_deadline_hours: int
    mandatory_custody_checkpoints: List[str]
    agreed_payment_amount: Decimal
    currency: str = "USD"
    quality_rejection_conditions: List[str]
    settlement_terms: str
    clauses: List[ContractClause]


class ContractExtractionRequest(BaseModel):
    contract_text: Optional[str] = None
    sample_id: Optional[str] = None


class ContractExtractionResponse(BaseModel):
    contract: PharmaContract
    ai_mode: str = Field(..., description="'LIVE_GEMINI' or 'DEMO_SIMULATION'")
    extraction_timestamp: datetime
    model_name: str


class LotEvaluation(BaseModel):
    lot_number: str
    medicine_name: str
    doses_count: int
    unit_price: Decimal
    allocated_amount: Decimal
    currency: str = "USD"
    temperature_status: str  # "PASS", "BREACH", "WARNING"
    evidence_status: str     # "VERIFIED", "HASH_MISMATCH", "MISSING"
    custody_status: str      # "INTACT", "GAP_DETECTED"
    recommendation: str      # "ELIGIBLE", "QUALITY_REVIEW", "INSUFFICIENT_EVIDENCE"
    rationale: str
    evidence_references: List[str]


class SettlementInvestigationResult(BaseModel):
    investigation_id: str
    shipment_id: str
    tracking_number: str
    contract_id: str
    contract_title: str
    carrier_name: str
    total_authorized_amount: Decimal
    currency: str = "USD"
    lots: List[LotEvaluation]
    overall_recommendation: str  # "ELIGIBLE_FOR_SETTLEMENT", "REQUIRES_QUALITY_REVIEW", "INSUFFICIENT_EVIDENCE"
    executive_summary: str
    compliance_breakdown: Dict[str, Any]
    investigation_timeline: List[Dict[str, Any]]
    ai_mode: str
    model_name: str
    generated_at: datetime


class HumanApprovalRequest(BaseModel):
    investigation_id: str
    shipment_id: str
    approved: bool
    approved_amount: Decimal
    reviewer_notes: str
    reviewer_id: str = "QA-AUDITOR-881"


class SettlementExecutionResponse(BaseModel):
    execution_id: str
    investigation_id: str
    shipment_id: str
    decision: str  # "APPROVED_AND_CAPTURED", "REJECTED_QUALITY_HOLD", "VOIDED"
    approved_amount: Decimal
    currency: str
    paypal_transaction_id: Optional[str] = None
    paypal_status: str
    is_live_sandbox: bool
    execution_timestamp: datetime
    idempotency_key: str
    notes: str
