"""CustodyEvent model tracking physical handovers and chain-of-custody transfers."""

import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from app.core.database import Base, UTCDateTime
from app.models.enums import CustodyEventType


class CustodyEvent(Base):
    __tablename__ = "custody_events"

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
    evidence_file_id = sa.Column(
        sa.String(36),
        nullable=True,
        index=True,
    )
    actor_user_id = sa.Column(
        sa.String(36),
        nullable=True,
        index=True,
    )
    event_type = sa.Column(
        sa.Enum(CustodyEventType, name="custody_event_type"),
        nullable=False,
    )
    carrier_name = sa.Column(sa.String(255), nullable=False)
    custodian_name = sa.Column(sa.String(255), nullable=False)
    location = sa.Column(sa.String(255), nullable=False)
    notes = sa.Column(sa.Text, nullable=True)
    recorded_at = sa.Column(UTCDateTime, nullable=False)
    created_at = sa.Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["shipment_id", "organization_id"],
            ["shipments.id", "shipments.organization_id"],
            name="fk_custody_shipment_org",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_custody_actor_user_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_file_id", "shipment_id"],
            ["evidence_files.id", "evidence_files.shipment_id"],
            name="fk_custody_evidence_shipment",
            ondelete="RESTRICT",
        ),
    )

    # Relationships
    shipment = relationship("Shipment", back_populates="custody_events", foreign_keys=[shipment_id, organization_id], viewonly=True)
    organization = relationship("Organization")
    actor_user = relationship("User", foreign_keys=[actor_user_id, organization_id], viewonly=True)
    evidence_file = relationship(
        "EvidenceFile",
        back_populates="custody_events",
        foreign_keys=[evidence_file_id, shipment_id],
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<CustodyEvent id={self.id} type={self.event_type} custodian={self.custodian_name}>"
