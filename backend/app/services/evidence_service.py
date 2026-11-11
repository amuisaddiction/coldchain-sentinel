"""Evidence service providing upload, SHA-256 integrity verification, and CSV telemetry extraction."""

import csv
import io
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.storage import compute_sha256, LocalStorageBackend
from app.core.config import settings
from app.models.evidence import EvidenceFile
from app.models.shipment import Shipment
from app.models.enums import EvidenceType, EvidenceIntegrityStatus
from app.schemas.evidence import EvidenceVerificationResponse
from app.services import temperature_service
from app.services.audit_service import log_audit_event


def get_storage():
    """Retrieve configured storage backend."""
    return LocalStorageBackend(base_path=settings.STORAGE_LOCAL_PATH)


def list_evidence_for_shipment(db: Session, org_id: str, shipment_id: str) -> List[EvidenceFile]:
    """List all evidence files for a shipment."""
    return list(
        db.scalars(
            select(EvidenceFile)
            .where(
                EvidenceFile.organization_id == org_id,
                EvidenceFile.shipment_id == shipment_id,
            )
            .order_by(EvidenceFile.created_at.desc())
        ).all()
    )


def get_evidence_by_id(db: Session, org_id: str, evidence_id: str) -> Optional[EvidenceFile]:
    """Retrieve evidence file strictly within caller's organization."""
    return db.scalar(
        select(EvidenceFile).where(
            EvidenceFile.organization_id == org_id,
            EvidenceFile.id == evidence_id,
        )
    )


def upload_evidence(
    db: Session,
    org_id: str,
    shipment_id: str,
    file_type: EvidenceType,
    original_filename: str,
    content: bytes,
    uploaded_by_user_id: str,
    client_ip: Optional[str] = None,
) -> EvidenceFile:
    """Upload evidence file, persist to storage, compute SHA-256, and extract telemetry if CSV."""
    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file payload cannot be empty",
        )

    shipment = db.scalar(
        select(Shipment).where(
            Shipment.organization_id == org_id,
            Shipment.id == shipment_id,
        )
    )
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found in your organization",
        )

    sha256_hash = compute_sha256(content)

    # Check for duplicate evidence in this shipment
    existing = db.scalar(
        select(EvidenceFile).where(
            EvidenceFile.shipment_id == shipment_id,
            EvidenceFile.sha256_hash == sha256_hash,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Identical evidence file has already been uploaded for this shipment",
        )

    storage = get_storage()
    storage_key, _, size_bytes = storage.save_file_sync(
        content=content,
        original_filename=original_filename,
        subfolder="evidence",
    )

    evidence = EvidenceFile(
        id=str(uuid.uuid4()),
        shipment_id=shipment.id,
        organization_id=org_id,
        file_type=file_type,
        original_filename=original_filename,
        storage_path=storage_key,
        file_size_bytes=size_bytes,
        sha256_hash=sha256_hash,
        integrity_status=EvidenceIntegrityStatus.VERIFIED,
        uploaded_by=uploaded_by_user_id,
        parsed_records_count=0,
    )
    db.add(evidence)
    db.flush()

    parsed_count = 0
    if file_type == EvidenceType.LOGGER_CSV:
        try:
            text_stream = io.StringIO(content.decode("utf-8"))
            reader = csv.DictReader(text_stream)
            raw_readings = []
            for row in reader:
                # Expecting 'timestamp' and 'temperature' (case-insensitive)
                row_lower = {k.lower().strip(): v.strip() for k, v in row.items() if k}
                ts_str = row_lower.get("timestamp") or row_lower.get("recorded_at") or row_lower.get("time")
                temp_str = row_lower.get("temperature") or row_lower.get("temp") or row_lower.get("temperature_celsius")
                sensor = row_lower.get("sensor_id") or "PRIMARY"

                if ts_str and temp_str:
                    try:
                        # Parse ISO or standard timestamp
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue

                    raw_readings.append({
                        "recorded_at": ts,
                        "temperature_celsius": Decimal(temp_str),
                        "sensor_id": sensor,
                    })

            if raw_readings:
                parsed_count = temperature_service.ingest_readings(
                    db=db,
                    shipment=shipment,
                    evidence_file_id=evidence.id,
                    raw_readings=raw_readings,
                )
                evidence.parsed_records_count = parsed_count
        except Exception:
            evidence.integrity_status = EvidenceIntegrityStatus.PARSING_FAILED

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=uploaded_by_user_id,
        shipment_id=shipment.id,
        entity_type="EVIDENCE",
        entity_id=evidence.id,
        action="EVIDENCE_UPLOAD",
        payload_after={
            "filename": original_filename,
            "sha256": sha256_hash,
            "parsed_records": parsed_count,
        },
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(evidence)
    return evidence


def verify_evidence_integrity(
    db: Session,
    org_id: str,
    evidence_id: str,
    client_ip: Optional[str] = None,
) -> EvidenceVerificationResponse:
    """Verify stored file against its recorded cryptographic SHA-256 digest to detect tampering."""
    evidence = get_evidence_by_id(db, org_id, evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file not found in your organization",
        )

    storage = get_storage()
    if not storage.exists_sync(evidence.storage_path):
        evidence.integrity_status = EvidenceIntegrityStatus.CORRUPTED
        db.commit()
        return EvidenceVerificationResponse(
            evidence_id=evidence.id,
            original_filename=evidence.original_filename,
            recorded_sha256=evidence.sha256_hash,
            computed_sha256="",
            is_tampered=True,
            integrity_status=EvidenceIntegrityStatus.CORRUPTED,
            message="Evidence file missing from physical storage",
        )

    content = storage.get_file_sync(evidence.storage_path)
    current_hash = compute_sha256(content)

    if current_hash == evidence.sha256_hash:
        evidence.integrity_status = EvidenceIntegrityStatus.VERIFIED
        is_tampered = False
        message = "Integrity verified: SHA-256 matches recorded evidence digest"
    else:
        evidence.integrity_status = EvidenceIntegrityStatus.HASH_MISMATCH
        is_tampered = True
        message = "TAMPER DETECTED: Computed SHA-256 does not match recorded evidence digest"

    log_audit_event(
        db=db,
        organization_id=org_id,
        entity_type="EVIDENCE",
        entity_id=evidence.id,
        action="INTEGRITY_VERIFICATION",
        payload_after={
            "status": evidence.integrity_status.value,
            "tampered": is_tampered,
        },
        ip_address=client_ip,
    )
    db.commit()

    return EvidenceVerificationResponse(
        evidence_id=evidence.id,
        original_filename=evidence.original_filename,
        recorded_sha256=evidence.sha256_hash,
        computed_sha256=current_hash,
        is_tampered=is_tampered,
        integrity_status=evidence.integrity_status,
        message=message,
    )
