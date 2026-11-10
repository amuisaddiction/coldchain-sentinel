"""ProductProfile model specifying cold-chain storage and telemetry rules."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy import event, inspect
from sqlalchemy.orm import relationship
from app.core.database import Base, UTCDateTime
from app.models.exceptions import ImmutableProfileError


class ProductProfile(Base):
    __tablename__ = "product_profiles"

    id = sa.Column(
        sa.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    organization_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = sa.Column(sa.String(255), nullable=False)
    version = sa.Column(sa.Integer, nullable=False, default=1)
    min_temperature_celsius = sa.Column(
        sa.Numeric(precision=5, scale=2, asdecimal=True),
        nullable=False,
    )
    max_temperature_celsius = sa.Column(
        sa.Numeric(precision=5, scale=2, asdecimal=True),
        nullable=False,
    )
    max_excursion_duration_seconds = sa.Column(sa.Integer, nullable=False, default=0)
    expected_sampling_interval_seconds = sa.Column(sa.Integer, nullable=False, default=300)
    max_sampling_gap_seconds = sa.Column(sa.Integer, nullable=False, default=600)
    is_active = sa.Column(sa.Boolean, nullable=False, default=True)
    is_locked = sa.Column(sa.Boolean, nullable=False, default=False)
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
        sa.UniqueConstraint("id", "organization_id", name="uq_product_profile_id_org"),
        sa.UniqueConstraint("organization_id", "name", "version", name="uq_org_product_profile_version"),
        sa.CheckConstraint("min_temperature_celsius < max_temperature_celsius", name="ck_product_profile_temp_range"),
        sa.CheckConstraint("expected_sampling_interval_seconds > 0", name="ck_profile_sampling_interval_positive"),
        sa.CheckConstraint("max_sampling_gap_seconds > 0", name="ck_profile_max_gap_positive"),
        sa.CheckConstraint(
            "max_sampling_gap_seconds >= expected_sampling_interval_seconds",
            name="ck_profile_gap_gte_interval",
        ),
        sa.CheckConstraint(
            "max_excursion_duration_seconds >= 0",
            name="ck_profile_excursion_non_negative",
        ),
    )

    # Relationships
    organization = relationship("Organization", back_populates="product_profiles")
    shipments = relationship(
        "Shipment",
        back_populates="product_profile",
        foreign_keys="[Shipment.product_profile_id, Shipment.organization_id]",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ProductProfile id={self.id} name={self.name} v={self.version} "
            f"range=[{self.min_temperature_celsius}, {self.max_temperature_celsius}] locked={self.is_locked}>"
        )


@event.listens_for(ProductProfile, "before_update")
def validate_product_profile_immutability(mapper, connection, target):
    """
    ORM-level validation preventing in-place mutations of compliance rules on locked profiles.
    Note: Direct raw SQL bulk updates bypass instance listeners; application service layer
    must maintain version increments.
    """
    # If the profile was already locked before this update
    state = inspect(target)
    locked_hist = state.attrs["is_locked"].history
    was_locked = locked_hist.unchanged[0] if locked_hist.unchanged else (
        locked_hist.deleted[0] if locked_hist.deleted else target.is_locked
    )

    if was_locked or target.is_locked:
        immutable_fields = [
            "min_temperature_celsius",
            "max_temperature_celsius",
            "max_excursion_duration_seconds",
            "expected_sampling_interval_seconds",
            "max_sampling_gap_seconds",
        ]
        for field in immutable_fields:
            hist = state.attrs[field].history
            if hist.has_changes():
                raise ImmutableProfileError(
                    f"Cannot update '{field}' on locked ProductProfile (id={target.id}, version={target.version}). "
                    f"Create a new profile version instead."
                )
