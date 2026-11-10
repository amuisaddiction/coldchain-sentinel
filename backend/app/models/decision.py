"""VerificationDecision model recording automated and auditor compliance evaluations."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from app.core.database import Base, UTCDateTime
from app.models.enums import DecisionType


class VerificationDecision(Base):
    __tablename__ = "verification_decisions"

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
    decision = sa.Column(
        sa.Enum(DecisionType, name="decision_type"),
        nullable=False,
    )
    confidence_score = sa.Column(
        sa.Numeric(precision=4, scale=3, asdecimal=True),
        nullable=False,
    )
    evidence_hash_snapshot = sa.Column(sa.String(64), nullable=False)
    temperature_rule_passed = sa.Column(sa.Boolean, nullable=False)
    custody_chain_passed = sa.Column(sa.Boolean, nullable=False)
    sampling_frequency_passed = sa.Column(sa.Boolean, nullable=False)
    total_excursion_seconds = sa.Column(sa.Integer, nullable=False)
    max_temperature_detected = sa.Column(
        sa.Numeric(precision=5, scale=2, asdecimal=True),
        nullable=True,
    )
    min_temperature_detected = sa.Column(
        sa.Numeric(precision=5, scale=2, asdecimal=True),
        nullable=True,
    )
    reasoning_summary = sa.Column(sa.Text, nullable=False)
    decided_by = sa.Column(
        sa.String(36),
        nullable=True,
        index=True,
    )
    created_at = sa.Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["shipment_id", "organization_id"],
            ["shipments.id", "shipments.organization_id"],
            name="fk_decision_shipment_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["decided_by", "organization_id"],
            ["users.id", "users.organization_id"],
            name="fk_decision_decided_by_org",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "confidence_score >= 0.000 AND confidence_score <= 1.000",
            name="ck_decision_confidence_score",
        ),
        sa.CheckConstraint(
            "total_excursion_seconds >= 0",
            name="ck_decision_excursion_non_negative",
        ),
    )

    # Relationships
    shipment = relationship("Shipment", back_populates="verification_decisions", foreign_keys=[shipment_id, organization_id], viewonly=True)
    organization = relationship("Organization")
    decided_by_user = relationship("User", foreign_keys=[decided_by, organization_id], viewonly=True)

    def __repr__(self) -> str:
        return f"<VerificationDecision id={self.id} shipment={self.shipment_id} decision={self.decision}>"
