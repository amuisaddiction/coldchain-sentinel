"""Payment and PaymentIdempotencyRecord models for payment assurance and idempotency."""

import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from app.core.database import Base, UTCDateTime, PortableJSON
from app.models.enums import PaymentStatus, PaymentAction, IdempotencyStatus


class Payment(Base):
    __tablename__ = "payments"

    id = sa.Column(
        sa.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    shipment_id = sa.Column(
        sa.String(36),
        unique=True,
        nullable=False,
        index=True,
    )
    organization_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payment_provider = sa.Column(sa.String(32), nullable=False, default="PAYPAL")
    paypal_order_id = sa.Column(sa.String(100), nullable=True, index=True)
    paypal_authorization_id = sa.Column(sa.String(100), nullable=True, index=True)
    paypal_capture_id = sa.Column(sa.String(100), nullable=True, index=True)
    amount_minor = sa.Column(sa.BigInteger, nullable=False)
    currency = sa.Column(sa.String(3), nullable=False)
    currency_exponent = sa.Column(sa.Integer, nullable=False)
    status = sa.Column(
        sa.Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.AUTHORIZED,
    )
    authorized_at = sa.Column(UTCDateTime, nullable=True)
    settled_at = sa.Column(UTCDateTime, nullable=True)
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
            name="fk_payment_shipment_org",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("amount_minor > 0", name="ck_payment_amount_positive"),
        sa.CheckConstraint(
            "currency_exponent >= 0 AND currency_exponent <= 4",
            name="ck_payment_currency_exponent_range",
        ),
        sa.CheckConstraint("payment_provider IN ('PAYPAL')", name="ck_payment_provider_valid"),
        sa.UniqueConstraint("payment_provider", "paypal_order_id", name="uq_payment_provider_order_id"),
        sa.UniqueConstraint(
            "payment_provider",
            "paypal_authorization_id",
            name="uq_payment_provider_auth_id",
        ),
        sa.UniqueConstraint(
            "payment_provider",
            "paypal_capture_id",
            name="uq_payment_provider_capture_id",
        ),
    )

    # Relationships
    shipment = relationship("Shipment", back_populates="payment", foreign_keys=[shipment_id, organization_id], viewonly=True)
    organization = relationship("Organization", back_populates="payments")
    idempotency_records = relationship(
        "PaymentIdempotencyRecord",
        back_populates="payment",
        passive_deletes="all",
    )

    def __repr__(self) -> str:
        return f"<Payment id={self.id} shipment={self.shipment_id} amount_minor={self.amount_minor} {self.currency} status={self.status}>"


class PaymentIdempotencyRecord(Base):
    __tablename__ = "payment_idempotency_records"

    id = sa.Column(
        sa.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    provider = sa.Column(sa.String(32), nullable=False, default="PAYPAL")
    action = sa.Column(
        sa.Enum(PaymentAction, name="payment_action"),
        nullable=False,
    )
    idempotency_key = sa.Column(sa.String(255), nullable=False)
    organization_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payment_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("payments.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    status = sa.Column(
        sa.Enum(IdempotencyStatus, name="idempotency_status"),
        nullable=False,
        default=IdempotencyStatus.IN_PROGRESS,
    )
    request_hash = sa.Column(sa.String(64), nullable=False)
    response_payload = sa.Column(PortableJSON(), nullable=True)
    response_status_code = sa.Column(sa.Integer, nullable=True)
    expires_at = sa.Column(UTCDateTime, nullable=False)
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
        sa.UniqueConstraint(
            "provider",
            "action",
            "idempotency_key",
            name="uq_payment_idempotency_provider_action_key",
        ),
    )

    # Relationships
    payment = relationship("Payment", back_populates="idempotency_records")
    organization = relationship("Organization")

    def __repr__(self) -> str:
        return f"<PaymentIdempotencyRecord id={self.id} provider={self.provider} action={self.action} key={self.idempotency_key} status={self.status}>"
