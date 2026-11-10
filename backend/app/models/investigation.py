"""Investigation model for dispute tracking and root-cause analysis."""

import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from app.core.database import Base, UTCDateTime
from app.models.enums import InvestigationStatus, InvestigationPriority


class Investigation(Base):
    __tablename__ = "investigations"

    id = sa.Column(
        sa.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    shipment_id = sa.Column(
        sa.String(36),
        nullable=False,
        index=True,
    )
    organization_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_to = sa.Column(
        sa.String(36),
        nullable=True,
        index=True,
    )
    status = sa.Column(
        sa.Enum(InvestigationStatus, name="investigation_status"),
        nullable=False,
        default=InvestigationStatus.OPEN,
    )
    priority = sa.Column(
        sa.Enum(InvestigationPriority, name="investigation_priority"),
        nullable=False,
        default=InvestigationPriority.MEDIUM,
    )
    findings = sa.Column(sa.Text, nullable=True)
    resolution_summary = sa.Column(sa.Text, nullable=True)
    opened_at = sa.Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    resolved_at = sa.Column(UTCDateTime, nullable=True)
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

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["shipment_id", "organization_id"],
            ["shipments.id", "shipments.organization_id"],
            name="fk_investigation_shipment_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_investigation_assigned_to_org",
            ondelete="RESTRICT",
        ),
    )

    # Relationships
    shipment = relationship("Shipment", back_populates="investigations", foreign_keys=[shipment_id, organization_id], viewonly=True)
    organization = relationship("Organization", back_populates="investigations")
    assignee = relationship("User", foreign_keys=[assigned_to, organization_id], viewonly=True)

    def __repr__(self) -> str:
        return f"<Investigation id={self.id} shipment={self.shipment_id} status={self.status} priority={self.priority}>"
