"""Payment idempotency key generation and validation primitives.

Requirement:
- Generate a stable unique idempotency key per payment operation.
- Persist it with a database unique constraint.
- Ensure repeated requests cannot create duplicate captures or voids.
- NEVER use an evidence file hash as the payment idempotency key.
"""

import hashlib
import uuid
from typing import Literal


PaymentActionType = Literal["CREATE_ORDER", "AUTHORIZE", "CAPTURE", "VOID"]


def generate_payment_idempotency_key(
    shipment_ref: str,
    action: PaymentActionType,
    authorization_id: str = "",
    nonce: str = ""
) -> str:
    """
    Generate a stable, collision-resistant idempotency key for payment operations.

    Structure:
    IDEMP-{shipment_ref}-{action}-{sha256(shipment_ref:action:auth_id:nonce)[:16]}

    Does NOT use evidence file hashes.
    """
    if not nonce:
        nonce = "default-op"

    raw_payload = f"{shipment_ref}:{action}:{authorization_id}:{nonce}".encode("utf-8")
    digest = hashlib.sha256(raw_payload).hexdigest()[:16]

    clean_ref = "".join(c for c in shipment_ref if c.isalnum() or c in ("-", "_")).upper()
    return f"IDEMP-{clean_ref}-{action}-{digest}"
