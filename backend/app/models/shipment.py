"""Shipment model with immutable temperature compliance rule snapshots."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy import event, inspect
from sqlalchemy.orm import relationship
from app.core.database import Base, UTCDateTime, PortableJSON
from app.models.enums import ShipmentStatus
from app.models.exceptions import ImmutableSnapshotError


class Shipment(Base):
    __tablename__ = "shipments"

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
    product_profile_id = sa.Column(
        sa.String(36),
        nullable=False,
        index=True,
    )
    created_by = sa.Column(
        sa.String(36),
        nullable=True,
        index=True,
    )
    tracking_number = sa.Column(sa.String(100), unique=True, index=True, nullable=False)
    status = sa.Column(
        sa.Enum(ShipmentStatus, name="shipment_status"),
        nullable=False,
        default=ShipmentStatus.CREATED,
    )
    origin = sa.Column(sa.String(255), nullable=False)
    destination = sa.Column(sa.String(255), nullable=False)
    dispatched_at = sa.Column(UTCDateTime, nullable=True)
    delivered_at = sa.Column(UTCDateTime, nullable=True)

    # Immutable Rule Snapshot Fields
    rule_profile_version = sa.Column(sa.Integer, nullable=False)
    rule_min_temperature_celsius = sa.Column(
        sa.Numeric(precision=5, scale=2, asdecimal=True),
        nullable=False,
    )
    rule_max_temperature_celsius = sa.Column(
        sa.Numeric(precision=5, scale=2, asdecimal=True),
        nullable=False,
    )
    rule_max_excursion_duration_seconds = sa.Column(sa.Integer, nullable=False)
    rule_expected_sampling_interval_seconds = sa.Column(sa.Integer, nullable=False)
    rule_max_sampling_gap_seconds = sa.Column(sa.Integer, nullable=False)
    rule_source_reference = sa.Column(sa.String(255), nullable=False)
    rule_snapshot_json = sa.Column(PortableJSON(), nullable=False)

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
        sa.UniqueConstraint("tracking_number", name="uq_shipment_tracking_number"),
        sa.UniqueConstraint("id", "organization_id", name="uq_shipments_id_org"),
        sa.ForeignKeyConstraint(
            ["product_profile_id", "organization_id"],
            ["product_profiles.id", "product_profiles.organization_id"],
            name="fk_shipment_product_profile_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_shipment_created_by_org",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "rule_min_temperature_celsius < rule_max_temperature_celsius",
            name="ck_shipment_rule_temp_range",
        ),
        sa.CheckConstraint(
            "rule_expected_sampling_interval_seconds > 0",
            name="ck_shipment_rule_sampling_positive",
        ),
        sa.CheckConstraint(
            "rule_max_sampling_gap_seconds > 0",
            name="ck_shipment_rule_gap_positive",
        ),
        sa.CheckConstraint(
            "rule_max_sampling_gap_seconds >= rule_expected_sampling_interval_seconds",
            name="ck_shipment_rule_gap_gte_interval",
        ),
        sa.CheckConstraint(
            "rule_max_excursion_duration_seconds >= 0",
            name="ck_shipment_rule_excursion_non_neg",
        ),
    )

    # Relationships
    organization = relationship("Organization", back_populates="shipments")
    product_profile = relationship(
        "ProductProfile",
        back_populates="shipments",
        foreign_keys=[product_profile_id, organization_id],
        viewonly=True,
    )
    creator = relationship(
        "User",
        foreign_keys=[created_by, organization_id],
        viewonly=True,
    )
    temperature_readings = relationship("TemperatureReading", back_populates="shipment", cascade="all, delete-orphan", foreign_keys="[TemperatureReading.shipment_id]")
    evidence_files = relationship("EvidenceFile", back_populates="shipment", foreign_keys="[EvidenceFile.shipment_id, EvidenceFile.organization_id]", viewonly=True)
    custody_events = relationship("CustodyEvent", back_populates="shipment", cascade="all, delete-orphan", foreign_keys="[CustodyEvent.shipment_id, CustodyEvent.organization_id]", viewonly=True)
    verification_decisions = relationship("VerificationDecision", back_populates="shipment", foreign_keys="[VerificationDecision.shipment_id, VerificationDecision.organization_id]", viewonly=True)
    payment = relationship("Payment", uselist=False, back_populates="shipment", foreign_keys="[Payment.shipment_id, Payment.organization_id]", viewonly=True)
    investigations = relationship("Investigation", back_populates="shipment", foreign_keys="[Investigation.shipment_id, Investigation.organization_id]", viewonly=True)

    def __repr__(self) -> str:
        return f"<Shipment id={self.id} tracking={self.tracking_number} status={self.status}>"


@event.listens_for(Shipment, "before_update")
def validate_shipment_rule_snapshot_immutability(mapper, connection, target):
    """
    ORM-level validation preventing modifications to frozen rule snapshot attributes after creation.
    Note: Direct raw SQL bulk updates bypass instance listeners.
    """
    state = inspect(target)
    snapshot_fields = [
        "rule_profile_version",
        "rule_min_temperature_celsius",
        "rule_max_temperature_celsius",
        "rule_max_excursion_duration_seconds",
        "rule_expected_sampling_interval_seconds",
        "rule_max_sampling_gap_seconds",
        "rule_source_reference",
        "rule_snapshot_json",
    ]
    for field in snapshot_fields:
        hist = state.attrs[field].history
        if hist.has_changes():
            raise ImmutableSnapshotError(
                f"Cannot modify immutable rule snapshot field '{field}' on Shipment (id={target.id})."
            )
