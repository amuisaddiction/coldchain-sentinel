"""Investigation service for incident inquiry tracking and audit report compilation."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.investigation import Investigation
from app.models.shipment import Shipment
from app.models.evidence import EvidenceFile
from app.models.decision import VerificationDecision
from app.models.enums import InvestigationStatus, InvestigationPriority
from app.services.temperature_service import get_temperature_summary
from app.services.audit_service import log_audit_event


def get_investigation_by_id(db: Session, org_id: str, investigation_id: str) -> Optional[Investigation]:
    """Retrieve investigation strictly scoped to caller's organization."""
    return db.scalar(
        select(Investigation).where(
            Investigation.organization_id == org_id,
            Investigation.id == investigation_id,
        )
    )


def list_investigations(
    db: Session,
    org_id: str,
    status_filter: Optional[InvestigationStatus] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Investigation]:
    """List investigations for caller's organization."""
    query = select(Investigation).where(Investigation.organization_id == org_id)
    if status_filter:
        query = query.where(Investigation.status == status_filter)
    query = query.offset(skip).limit(limit).order_by(Investigation.opened_at.desc())
    return list(db.scalars(query).all())


def create_investigation(
    db: Session,
    org_id: str,
    shipment_id: str,
    priority: InvestigationPriority = InvestigationPriority.MEDIUM,
    assigned_to: Optional[str] = None,
    findings: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> Investigation:
    """Open a new formal investigation into a shipment excursion or discrepancy."""
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

    now = datetime.now(timezone.utc)
    investigation = Investigation(
        id=str(uuid.uuid4()),
        shipment_id=shipment.id,
        organization_id=org_id,
        assigned_to=assigned_to,
        status=InvestigationStatus.OPEN,
        priority=priority,
        findings=findings.strip() if findings else None,
        opened_at=now,
    )
    db.add(investigation)
    db.flush()

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=actor_user_id,
        shipment_id=shipment.id,
        entity_type="INVESTIGATION",
        entity_id=investigation.id,
        action="INVESTIGATION_OPENED",
        payload_after={"priority": priority.value, "assigned_to": assigned_to},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(investigation)
    return investigation


def update_investigation(
    db: Session,
    org_id: str,
    investigation_id: str,
    new_status: Optional[InvestigationStatus] = None,
    new_priority: Optional[InvestigationPriority] = None,
    assigned_to: Optional[str] = None,
    findings: Optional[str] = None,
    resolution_summary: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> Investigation:
    """Update investigation details and resolve status."""
    inv = get_investigation_by_id(db, org_id, investigation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found in your organization",
        )

    old_status = inv.status
    if new_status:
        inv.status = new_status
        if new_status in (InvestigationStatus.RESOLVED_APPROVED, InvestigationStatus.RESOLVED_REJECTED):
            inv.resolved_at = datetime.now(timezone.utc)

    if new_priority:
        inv.priority = new_priority
    if assigned_to is not None:
        inv.assigned_to = assigned_to
    if findings is not None:
        inv.findings = findings
    if resolution_summary is not None:
        inv.resolution_summary = resolution_summary

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=actor_user_id,
        shipment_id=inv.shipment_id,
        entity_type="INVESTIGATION",
        entity_id=inv.id,
        action="INVESTIGATION_UPDATED",
        payload_before={"status": old_status.value},
        payload_after={"status": inv.status.value},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(inv)
    return inv


def generate_investigation_report(
    db: Session,
    org_id: str,
    investigation_id: str,
) -> Dict[str, Any]:
    """Compile an authenticated investigation incident report from stored database records."""
    inv = get_investigation_by_id(db, org_id, investigation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found in your organization",
        )

    shipment = db.scalar(select(Shipment).where(Shipment.id == inv.shipment_id))
    temp_summary = get_temperature_summary(db=db, org_id=org_id, shipment_id=inv.shipment_id)

    evidence_records = list(
        db.scalars(
            select(EvidenceFile).where(EvidenceFile.shipment_id == inv.shipment_id)
        ).all()
    )

    decisions = list(
        db.scalars(
            select(VerificationDecision).where(VerificationDecision.shipment_id == inv.shipment_id)
        ).all()
    )

    return {
        "investigation_id": inv.id,
        "shipment_id": inv.shipment_id,
        "organization_id": inv.organization_id,
        "tracking_number": shipment.tracking_number if shipment else "",
        "status": inv.status,
        "priority": inv.priority,
        "findings": inv.findings,
        "resolution_summary": inv.resolution_summary,
        "shipment_details": {
            "origin": shipment.origin if shipment else "",
            "destination": shipment.destination if shipment else "",
            "status": shipment.status.value if shipment else "",
            "dispatched_at": shipment.dispatched_at.isoformat() if shipment and shipment.dispatched_at else None,
            "delivered_at": shipment.delivered_at.isoformat() if shipment and shipment.delivered_at else None,
            "rule_min_temp": str(shipment.rule_min_temperature_celsius) if shipment else "",
            "rule_max_temp": str(shipment.rule_max_temperature_celsius) if shipment else "",
            "max_excursion_seconds": shipment.rule_max_excursion_duration_seconds if shipment else 0,
        },
        "temperature_summary": temp_summary.model_dump(),
        "evidence_artifacts": [
            {
                "id": e.id,
                "filename": e.original_filename,
                "sha256": e.sha256_hash,
                "status": e.integrity_status.value,
                "records_count": e.parsed_records_count,
            }
            for e in evidence_records
        ],
        "verification_decisions": [
            {
                "id": d.id,
                "decision": d.decision.value,
                "confidence_score": str(d.confidence_score),
                "total_excursion_seconds": d.total_excursion_seconds,
                "temperature_passed": d.temperature_rule_passed,
                "reasoning": d.reasoning_summary,
                "created_at": d.created_at.isoformat(),
            }
            for d in decisions
        ],
        "generated_at": datetime.now(timezone.utc),
    }
