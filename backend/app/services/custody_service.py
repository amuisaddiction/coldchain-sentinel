"""Chain of Custody service managing physical handover events and actor verification."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.custody import CustodyEvent
from app.models.shipment import Shipment
from app.models.evidence import EvidenceFile
from app.models.enums import CustodyEventType
from app.services.audit_service import log_audit_event


def list_custody_events(db: Session, org_id: str, shipment_id: str) -> List[CustodyEvent]:
    """Retrieve immutable chain of custody events ordered chronologically."""
    return list(
        db.scalars(
            select(CustodyEvent)
            .where(
                CustodyEvent.organization_id == org_id,
                CustodyEvent.shipment_id == shipment_id,
            )
            .order_by(CustodyEvent.recorded_at.asc())
        ).all()
    )


def record_custody_transfer(
    db: Session,
    org_id: str,
    shipment_id: str,
    event_type: CustodyEventType,
    carrier_name: str,
    custodian_name: str,
    location: str,
    recorded_at: Optional[datetime] = None,
    evidence_file_id: Optional[str] = None,
    notes: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> CustodyEvent:
    """Record a verified physical custody transfer."""
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

    if evidence_file_id:
        ev = db.scalar(
            select(EvidenceFile).where(
                EvidenceFile.id == evidence_file_id,
                EvidenceFile.shipment_id == shipment_id,
            )
        )
        if not ev:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evidence file does not belong to this shipment",
            )

    event_time = recorded_at or datetime.now(timezone.utc)

    event = CustodyEvent(
        id=str(uuid.uuid4()),
        shipment_id=shipment.id,
        organization_id=org_id,
        evidence_file_id=evidence_file_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        carrier_name=carrier_name.strip(),
        custodian_name=custodian_name.strip(),
        location=location.strip(),
        notes=notes.strip() if notes else None,
        recorded_at=event_time,
    )
    db.add(event)
    db.flush()

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=actor_user_id,
        shipment_id=shipment.id,
        entity_type="CUSTODY_EVENT",
        entity_id=event.id,
        action="CUSTODY_TRANSFER",
        payload_after={
            "type": event_type.value,
            "carrier": carrier_name,
            "custodian": custodian_name,
            "location": location,
        },
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(event)
    return event
