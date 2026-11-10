"""Organization model representing the multi-tenant isolation boundary."""

import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from app.core.database import Base, UTCDateTime
from app.models.enums import OrganizationStatus


class Organization(Base):
    __tablename__ = "organizations"

    id = sa.Column(
        sa.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    name = sa.Column(sa.String(255), nullable=False)
    slug = sa.Column(sa.String(100), unique=True, index=True, nullable=False)
    status = sa.Column(
        sa.Enum(OrganizationStatus, name="organization_status"),
        nullable=False,
        default=OrganizationStatus.ACTIVE,
    )
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

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    product_profiles = relationship("ProductProfile", back_populates="organization", cascade="all, delete-orphan")
    shipments = relationship("Shipment", back_populates="organization")
    evidence_files = relationship("EvidenceFile", back_populates="organization")
    payments = relationship("Payment", back_populates="organization")
    investigations = relationship("Investigation", back_populates="organization")
    audit_events = relationship("AuditEvent", back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} slug={self.slug} status={self.status}>"
