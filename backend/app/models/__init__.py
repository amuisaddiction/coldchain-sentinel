"""ColdChain Sentinel Relational Models Package."""

from app.models.enums import (
    OrganizationStatus,
    UserRole,
    ShipmentStatus,
    EvidenceType,
    EvidenceIntegrityStatus,
    TemperatureSeverity,
    CustodyEventType,
    DecisionType,
    PaymentStatus,
    PaymentAction,
    IdempotencyStatus,
    InvestigationStatus,
    InvestigationPriority,
    OutboxStatus,
)
from app.models.exceptions import (
    ImmutableProfileError,
    ImmutableSnapshotError,
)
from app.models.organization import Organization
from app.models.user import User
from app.models.product_profile import ProductProfile
from app.models.shipment import Shipment
from app.models.evidence import EvidenceFile
from app.models.temperature import TemperatureReading
from app.models.custody import CustodyEvent
from app.models.decision import VerificationDecision
from app.models.payment import Payment, PaymentIdempotencyRecord
from app.models.investigation import Investigation
from app.models.audit import AuditEvent
from app.models.outbox import OutboxEvent

__all__ = [
    # Enums
    "OrganizationStatus",
    "UserRole",
    "ShipmentStatus",
    "EvidenceType",
    "EvidenceIntegrityStatus",
    "TemperatureSeverity",
    "CustodyEventType",
    "DecisionType",
    "PaymentStatus",
    "PaymentAction",
    "IdempotencyStatus",
    "InvestigationStatus",
    "InvestigationPriority",
    "OutboxStatus",
    # Exceptions
    "ImmutableProfileError",
    "ImmutableSnapshotError",
    # 13 Models
    "Organization",
    "User",
    "ProductProfile",
    "Shipment",
    "EvidenceFile",
    "TemperatureReading",
    "CustodyEvent",
    "VerificationDecision",
    "Payment",
    "PaymentIdempotencyRecord",
    "Investigation",
    "AuditEvent",
    "OutboxEvent",
]
