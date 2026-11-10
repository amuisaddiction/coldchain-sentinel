"""AuditEvent model providing an append-only application audit log."""

import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from app.core.database import Base, UTCDateTime, PortableJSON


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = sa.Column(
        sa.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    organization_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id = sa.Column(
        sa.String(36),
        nullable=True,
        index=True,
    )
    shipment_id = sa.Column(
        sa.String(36),
        nullable=True,
        index=True,
    )
    entity_type = sa.Column(sa.String(50), nullable=False)
    entity_id = sa.Column(sa.String(36), nullable=False, index=True)
    action = sa.Column(sa.String(50), nullable=False)
    payload_before = sa.Column(PortableJSON(), nullable=True)
    payload_after = sa.Column(PortableJSON(), nullable=True)
    ip_address = sa.Column(sa.String(45), nullable=True)
    created_at = sa.Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["user_id", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_audit_user_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["shipment_id", "organization_id"],
            ["shipments.id", "shipments.organization_id"],
            name="fk_audit_shipment_org",
            ondelete="RESTRICT",
        ),
    )

    # Relationships
    organization = relationship("Organization", back_populates="audit_events")
    user = relationship("User", foreign_keys=[user_id, organization_id], viewonly=True)
    shipment = relationship("Shipment", foreign_keys=[shipment_id, organization_id], viewonly=True)

    def __repr__(self) -> str:
        return f"<AuditEvent id={self.id} entity={self.entity_type} action={self.action} user={self.user_id}>"
