"""Outbox event model for reliable transaction-bound asynchronous event dispatch."""

import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from app.core.database import Base, UTCDateTime, PortableJSON
from app.models.enums import OutboxStatus


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = sa.Column(
        sa.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    event_type = sa.Column(sa.String(100), nullable=False, index=True)
    aggregate_type = sa.Column(sa.String(50), nullable=False)
    aggregate_id = sa.Column(sa.String(36), nullable=False, index=True)
    payload = sa.Column(PortableJSON(), nullable=False)
    status = sa.Column(
        sa.Enum(OutboxStatus, name="outbox_status"),
        nullable=False,
        default=OutboxStatus.PENDING,
        index=True,
    )
    available_at = sa.Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    claim_token = sa.Column(sa.String(36), nullable=True)
    lease_until = sa.Column(UTCDateTime, nullable=True, index=True)
    attempts = sa.Column(sa.Integer, nullable=False, default=0)
    max_attempts = sa.Column(sa.Integer, nullable=False, default=5)
    processed_at = sa.Column(UTCDateTime, nullable=True)
    last_error = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = sa.Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<OutboxEvent id={self.id} event={self.event_type} status={self.status} attempts={self.attempts}>"
