"""TemperatureReading model representing telemetry points extracted from evidence."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from app.core.database import Base, UTCDateTime, PortableJSON
from app.models.enums import TemperatureSeverity


class TemperatureReading(Base):
    __tablename__ = "temperature_readings"

    id = sa.Column(
        sa.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    shipment_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_file_id = sa.Column(
        sa.String(36),
        nullable=False,
        index=True,
    )
    row_number = sa.Column(sa.Integer, nullable=False)
    sensor_id = sa.Column(sa.String(100), nullable=False, default="PRIMARY")
    recorded_at = sa.Column(UTCDateTime, nullable=False)
    temperature_celsius = sa.Column(
        sa.Numeric(precision=5, scale=2, asdecimal=True),
        nullable=False,
    )
    severity = sa.Column(
        sa.Enum(TemperatureSeverity, name="temperature_severity"),
        nullable=False,
        default=TemperatureSeverity.NORMAL,
    )
    sequence_number = sa.Column(sa.Integer, nullable=True)
    raw_reading_metadata = sa.Column(PortableJSON(), nullable=True)
    created_at = sa.Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["evidence_file_id", "shipment_id"],
            ["evidence_files.id", "evidence_files.shipment_id"],
            name="fk_reading_evidence_shipment",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("evidence_file_id", "row_number", name="uq_reading_evidence_row"),
        sa.Index("ix_temp_readings_shipment_time", "shipment_id", "recorded_at"),
        sa.Index("ix_temp_readings_sensor_time", "shipment_id", "sensor_id", "recorded_at"),
        sa.CheckConstraint("row_number > 0", name="ck_reading_row_number_positive"),
        sa.CheckConstraint(
            "sequence_number IS NULL OR sequence_number >= 0",
            name="ck_reading_sequence_non_negative",
        ),
    )

    # Relationships
    shipment = relationship("Shipment", back_populates="temperature_readings", foreign_keys=[shipment_id])
    evidence_file = relationship(
        "EvidenceFile",
        back_populates="temperature_readings",
        foreign_keys=[evidence_file_id, shipment_id],
        viewonly=True,
    )

    def __repr__(self) -> str:
        return (
            f"<TemperatureReading id={self.id} shipment={self.shipment_id} "
            f"sensor={self.sensor_id} temp={self.temperature_celsius} severity={self.severity}>"
        )
