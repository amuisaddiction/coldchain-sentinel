"""Shipment management service with immutable rule snapshots and status state machine."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.shipment import Shipment
from app.models.product_profile import ProductProfile
from app.models.enums import ShipmentStatus
from app.services.product_profile_service import get_profile_by_id
from app.services.audit_service import log_audit_event

VALID_TRANSITIONS = {
    ShipmentStatus.CREATED: {ShipmentStatus.IN_TRANSIT, ShipmentStatus.CANCELLED},
    ShipmentStatus.IN_TRANSIT: {ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED},
    ShipmentStatus.DELIVERED: {ShipmentStatus.VERIFIED, ShipmentStatus.FAILED},
    ShipmentStatus.VERIFIED: set(),
    ShipmentStatus.FAILED: set(),
    ShipmentStatus.CANCELLED: set(),
}


def get_shipment_by_id(db: Session, org_id: str, shipment_id: str) -> Optional[Shipment]:
    """Retrieve shipment strictly scoped to organization."""
    return db.scalar(
        select(Shipment).where(
            Shipment.organization_id == org_id,
            Shipment.id == shipment_id,
        )
    )


def list_shipments(
    db: Session,
    org_id: str,
    status_filter: Optional[ShipmentStatus] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Shipment]:
    """List shipments within organization with optional status filtering."""
    query = select(Shipment).where(Shipment.organization_id == org_id)
    if status_filter:
        query = query.where(Shipment.status == status_filter)
    query = query.offset(skip).limit(limit).order_by(Shipment.created_at.desc())
    return list(db.scalars(query).all())


def create_shipment(
    db: Session,
    org_id: str,
    product_profile_id: str,
    tracking_number: str,
    origin: str,
    destination: str,
    created_by_user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> Shipment:
    """Create shipment with immutable compliance snapshot and lock profile."""
    # Check duplicate tracking number
    existing_tracking = db.scalar(select(Shipment).where(Shipment.tracking_number == tracking_number.strip()))
    if existing_tracking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tracking number '{tracking_number}' is already registered",
        )

    # Validate product profile strictly within caller's organization
    profile = get_profile_by_id(db, org_id, product_profile_id)
    if not profile or not profile.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active product profile not found in your organization",
        )

    # Lock profile upon shipment creation
    profile.is_locked = True

    # Build snapshot payload
    snapshot_json = {
        "profile_id": profile.id,
        "name": profile.name,
        "version": profile.version,
        "min_temperature_celsius": str(profile.min_temperature_celsius),
        "max_temperature_celsius": str(profile.max_temperature_celsius),
        "max_excursion_duration_seconds": profile.max_excursion_duration_seconds,
        "expected_sampling_interval_seconds": profile.expected_sampling_interval_seconds,
        "max_sampling_gap_seconds": profile.max_sampling_gap_seconds,
        "snapshotted_at": datetime.now(timezone.utc).isoformat(),
    }

    shipment = Shipment(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        product_profile_id=profile.id,
        created_by=created_by_user_id,
        tracking_number=tracking_number.strip(),
        status=ShipmentStatus.CREATED,
        origin=origin.strip(),
        destination=destination.strip(),
        rule_profile_version=profile.version,
        rule_min_temperature_celsius=profile.min_temperature_celsius,
        rule_max_temperature_celsius=profile.max_temperature_celsius,
        rule_max_excursion_duration_seconds=profile.max_excursion_duration_seconds,
        rule_expected_sampling_interval_seconds=profile.expected_sampling_interval_seconds,
        rule_max_sampling_gap_seconds=profile.max_sampling_gap_seconds,
        rule_source_reference=f"profile:{profile.id}:v{profile.version}",
        rule_snapshot_json=snapshot_json,
    )
    db.add(shipment)
    db.flush()

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=created_by_user_id,
        shipment_id=shipment.id,
        entity_type="SHIPMENT",
        entity_id=shipment.id,
        action="SHIPMENT_CREATE",
        payload_after={"tracking_number": shipment.tracking_number, "status": shipment.status.value},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(shipment)
    return shipment


def update_shipment_status(
    db: Session,
    org_id: str,
    shipment_id: str,
    new_status: ShipmentStatus,
    actor_user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> Shipment:
    """Transition shipment lifecycle status enforcing strict state machine transitions."""
    shipment = get_shipment_by_id(db, org_id, shipment_id)
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found in your organization",
        )

    current_status = shipment.status
    allowed_next = VALID_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition from {current_status.value} to {new_status.value}",
        )

    now = datetime.now(timezone.utc)
    if new_status == ShipmentStatus.IN_TRANSIT and not shipment.dispatched_at:
        shipment.dispatched_at = now
    elif new_status == ShipmentStatus.DELIVERED and not shipment.delivered_at:
        shipment.delivered_at = now

    shipment.status = new_status

    log_audit_event(
        db=db,
        organization_id=org_id,
        user_id=actor_user_id,
        shipment_id=shipment.id,
        entity_type="SHIPMENT",
        entity_id=shipment.id,
        action="SHIPMENT_STATUS_UPDATE",
        payload_before={"status": current_status.value},
        payload_after={"status": new_status.value},
        ip_address=client_ip,
    )
    db.commit()
    db.refresh(shipment)
    return shipment
