"""Evidence schemas for upload, display, and integrity checks."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import EvidenceType, EvidenceIntegrityStatus


class EvidenceFileResponse(BaseModel):
    id: str
    shipment_id: str
    organization_id: str
    file_type: EvidenceType
    original_filename: str
    storage_path: str
    file_size_bytes: int
    sha256_hash: str
    integrity_status: EvidenceIntegrityStatus
    uploaded_by: str
    parsed_records_count: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceVerificationResponse(BaseModel):
    evidence_id: str
    original_filename: str
    recorded_sha256: str
    computed_sha256: str
    is_tampered: bool
    integrity_status: EvidenceIntegrityStatus
    message: str
