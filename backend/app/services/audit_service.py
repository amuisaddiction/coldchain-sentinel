"""Audit logging service for tracking system mutations and security events."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent


def log_audit_event(
    db: Session,
    organization_id: str,
    entity_type: str,
    entity_id: str,
    action: str,
    user_id: Optional[str] = None,
    shipment_id: Optional[str] = None,
    payload_before: Optional[Dict[str, Any]] = None,
    payload_after: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AuditEvent:
    """Create and persist an append-only AuditEvent record."""
    event = AuditEvent(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        user_id=user_id,
        shipment_id=shipment_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        payload_before=payload_before,
        payload_after=payload_after,
        ip_address=ip_address,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    return event
