"""Reliable outbox event dispatcher with per-event claim tokens, lease fencing, and exponential retry backoff."""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_

from app.models.outbox import OutboxEvent
from app.models.enums import OutboxStatus
from app.services import payment_service

logger = logging.getLogger(__name__)


def claim_pending_events(
    db: Session,
    batch_size: int = 10,
    lease_seconds: int = 60,
) -> List[Tuple[OutboxEvent, str]]:
    """
    Claim a batch of eligible outbox events assigning a distinct unique fencing claim token per event.
    Eligible: PENDING with available_at <= now, or PROCESSING with lease_until < now (expired lease recovery).
    """
    now = datetime.now(timezone.utc)

    # Find claimable event IDs
    query = (
        select(OutboxEvent)
        .where(
            or_(
                and_(
                    OutboxEvent.status == OutboxStatus.PENDING,
                    OutboxEvent.available_at <= now,
                ),
                and_(
                    OutboxEvent.status == OutboxStatus.PROCESSING,
                    OutboxEvent.lease_until < now,
                ),
            )
        )
        .limit(batch_size)
    )

    events = list(db.scalars(query).all())
    claimed: List[Tuple[OutboxEvent, str]] = []

    for ev in events:
        token = str(uuid.uuid4())
        ev.status = OutboxStatus.PROCESSING
        ev.claim_token = token
        ev.lease_until = now + timedelta(seconds=lease_seconds)
        ev.attempts += 1
        claimed.append((ev, token))

    db.commit()
    for ev, token in claimed:
        db.refresh(ev)

    return claimed


def process_claimed_event(
    db: Session,
    event_id: str,
    claim_token: str,
) -> bool:
    """
    Process a single claimed event verifying lease fencing ownership.
    Guarantees stale workers whose lease expired cannot overwrite state.
    """
    ev = db.scalar(
        select(OutboxEvent).where(
            OutboxEvent.id == event_id,
            OutboxEvent.claim_token == claim_token,
            OutboxEvent.status == OutboxStatus.PROCESSING,
        )
    )
    if not ev:
        logger.warning(
            "Worker fencing rejected: Event %s no longer owned by claim token %s",
            event_id,
            claim_token,
        )
        return False

    try:
        # Handler dispatch
        if ev.event_type == "PAYMENT_CAPTURE":
            payload = ev.payload or {}
            payment_service.execute_capture(
                db=db,
                payment_id=payload["payment_id"],
                idempotency_key=payload["idempotency_key"],
            )
        else:
            logger.info("Generic event dispatched: %s", ev.event_type)

        now = datetime.now(timezone.utc)
        ev.status = OutboxStatus.COMPLETED
        ev.processed_at = now
        ev.claim_token = None
        ev.lease_until = None
        db.commit()
        return True

    except Exception as exc:
        logger.error("Outbox dispatch failure for event %s: %s", event_id, exc)
        db.rollback()

        # Re-fetch event to update failure status
        ev = db.scalar(
            select(OutboxEvent).where(
                OutboxEvent.id == event_id,
                OutboxEvent.claim_token == claim_token,
            )
        )
        if ev:
            now = datetime.now(timezone.utc)
            ev.last_error = str(exc)
            if ev.attempts >= ev.max_attempts:
                ev.status = OutboxStatus.DEAD_LETTER
                ev.claim_token = None
                ev.lease_until = None
            else:
                # Exponential retry backoff: 2^(attempts-1) * 10 seconds
                backoff_seconds = (2 ** (ev.attempts - 1)) * 10
                ev.available_at = now + timedelta(seconds=backoff_seconds)
                ev.status = OutboxStatus.PENDING
                ev.claim_token = None
                ev.lease_until = None

            db.commit()
        return False


def run_outbox_cycle(db: Session, batch_size: int = 10) -> int:
    """Execute one complete claim-and-dispatch processing cycle."""
    claimed = claim_pending_events(db=db, batch_size=batch_size)
    processed_count = 0
    for ev, token in claimed:
        success = process_claimed_event(db=db, event_id=ev.id, claim_token=token)
        if success:
            processed_count += 1
    return processed_count
