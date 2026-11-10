"""EvidenceFile model representing uploaded logger CSVs, manifests, and certificates."""

import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from app.core.database import Base, UTCDateTime
from app.models.enums import EvidenceType, EvidenceIntegrityStatus


class EvidenceFile(Base):
    __tablename__ = "evidence_files"

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
    file_type = sa.Column(
        sa.Enum(EvidenceType, name="evidence_type"),
        nullable=False,
    )
    original_filename = sa.Column(sa.String(255), nullable=False)
    storage_path = sa.Column(sa.String(500), nullable=False)
    file_size_bytes = sa.Column(sa.BigInteger, nullable=False)
    sha256_hash = sa.Column(sa.String(64), nullable=False, index=True)
    integrity_status = sa.Column(
        sa.Enum(EvidenceIntegrityStatus, name="evidence_integrity_status"),
        nullable=False,
        default=EvidenceIntegrityStatus.VERIFIED,
    )
    uploaded_by = sa.Column(
        sa.String(36),
        nullable=False,
        index=True,
    )
    parsed_records_count = sa.Column(sa.Integer, nullable=True)
    created_at = sa.Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        sa.UniqueConstraint("id", "shipment_id", name="uq_evidence_files_id_shipment"),
        sa.UniqueConstraint("shipment_id", "sha256_hash", name="uq_shipment_evidence_hash"),
        sa.ForeignKeyConstraint(
            ["shipment_id", "organization_id"],
            ["shipments.id", "shipments.organization_id"],
            name="fk_evidence_shipment_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_evidence_uploaded_by_org",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("file_size_bytes > 0", name="ck_evidence_file_size_positive"),
    )

    # Relationships
    shipment = relationship("Shipment", back_populates="evidence_files", foreign_keys=[shipment_id, organization_id], viewonly=True)
    organization = relationship("Organization", back_populates="evidence_files")
    uploader = relationship("User", foreign_keys=[uploaded_by, organization_id], viewonly=True)
    temperature_readings = relationship(
        "TemperatureReading",
        back_populates="evidence_file",
        cascade="all, delete-orphan",
        foreign_keys="[TemperatureReading.evidence_file_id, TemperatureReading.shipment_id]",
        viewonly=True,
    )
    custody_events = relationship(
        "CustodyEvent",
        back_populates="evidence_file",
        foreign_keys="[CustodyEvent.evidence_file_id, CustodyEvent.shipment_id]",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<EvidenceFile id={self.id} filename={self.original_filename} status={self.integrity_status}>"
