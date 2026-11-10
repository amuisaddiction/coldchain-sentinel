"""Core system enums for ColdChain Sentinel."""

import enum


class OrganizationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    QUALITY_ASSURANCE = "QUALITY_ASSURANCE"
    OPERATOR = "OPERATOR"
    AUDITOR = "AUDITOR"
    VIEWER = "VIEWER"


class ShipmentStatus(str, enum.Enum):
    CREATED = "CREATED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class EvidenceType(str, enum.Enum):
    LOGGER_CSV = "LOGGER_CSV"
    CALIBRATION_CERTIFICATE = "CALIBRATION_CERTIFICATE"
    DELIVERY_MANIFEST = "DELIVERY_MANIFEST"
    INSPECTION_PHOTO = "INSPECTION_PHOTO"


class EvidenceIntegrityStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    HASH_MISMATCH = "HASH_MISMATCH"
    CORRUPTED = "CORRUPTED"
    PARSING_FAILED = "PARSING_FAILED"


class TemperatureSeverity(str, enum.Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL_EXCURSION = "CRITICAL_EXCURSION"


class CustodyEventType(str, enum.Enum):
    DISPATCH = "DISPATCH"
    AIRPORT_TRANSFER = "AIRPORT_TRANSFER"
    CUSTOMS_CLEARANCE = "CUSTOMS_CLEARANCE"
    LAST_MILE_PICKUP = "LAST_MILE_PICKUP"
    DELIVERY_HANDOVER = "DELIVERY_HANDOVER"


class DecisionType(str, enum.Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


class PaymentStatus(str, enum.Enum):
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    VOIDED = "VOIDED"
    HELD_FOR_REVIEW = "HELD_FOR_REVIEW"
    FAILED = "FAILED"


class PaymentAction(str, enum.Enum):
    CAPTURE = "CAPTURE"
    VOID = "VOID"
    REFUND = "REFUND"


class IdempotencyStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REQUIRES_RECONCILIATION = "REQUIRES_RECONCILIATION"


class InvestigationStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED_APPROVED = "RESOLVED_APPROVED"
    RESOLVED_REJECTED = "RESOLVED_REJECTED"


class InvestigationPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
