"""Security and authentication utilities.

Provides bcrypt password hashing and PyJWT token generation and verification
with strict claim validation, forward clock skew tolerance, and canonical UUID checks.
"""

import math
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
import bcrypt
import jwt
from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_TIMESTAMP = 253402300799  # Year 9999-12-31T23:59:59Z
CLOCK_SKEW_TOLERANCE_SECONDS = 30


class SecurityError(Exception):
    """Base exception for security and authentication failures."""
    pass


class InvalidTokenError(SecurityError):
    """Raised when a JWT token is invalid, expired, tampered, or malformed."""
    pass


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with 12 salt rounds."""
    if not isinstance(password, str) or len(password) == 0:
        raise ValueError("Password must be a non-empty string")
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception as exc:
        logger.warning("Password verification encountered an error: %s", type(exc).__name__)
        return False


def _validate_numeric_timestamp(val: Any, field_name: str) -> float:
    """Validate numeric timestamp bounds and type safely."""
    if isinstance(val, bool):
        raise InvalidTokenError(f"Claim '{field_name}' cannot be boolean")
    if not isinstance(val, (int, float)):
        raise InvalidTokenError(f"Claim '{field_name}' must be numeric")
    if math.isnan(val) or math.isinf(val):
        raise InvalidTokenError(f"Claim '{field_name}' cannot be NaN or infinite")
    if val < 0 or val > MAX_TIMESTAMP:
        raise InvalidTokenError(f"Claim '{field_name}' out of safe range [0, {MAX_TIMESTAMP}]")
    return float(val)


def _validate_canonical_uuid(val: Any, field_name: str) -> str:
    """Validate canonical lowercase UUIDv4 string."""
    if not isinstance(val, str):
        raise InvalidTokenError(f"Claim '{field_name}' must be a string")
    try:
        parsed = uuid.UUID(val, version=4)
    except (ValueError, AttributeError, TypeError):
        raise InvalidTokenError(f"Claim '{field_name}' is not a valid UUIDv4")
    canonical = str(parsed).lower()
    if val != canonical:
        raise InvalidTokenError(f"Claim '{field_name}' is not in canonical lowercase format")
    return canonical


def create_access_token(
    user_id: str,
    org_id: str,
    role: str,
    token_version: int = 1,
    auth_version: int = 1,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a cryptographically signed PyJWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    sub_canonical = _validate_canonical_uuid(user_id, "user_id")
    org_canonical = _validate_canonical_uuid(org_id, "org_id")
    jti_canonical = str(uuid.uuid4()).lower()

    payload: Dict[str, Any] = {
        "sub": sub_canonical,
        "org_id": org_canonical,
        "role": str(role),
        "token_version": int(token_version),
        "auth_version": int(auth_version),
        "type": "access",
        "jti": jti_canonical,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    token = jwt.encode(
        payload,
        settings.APP_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def create_refresh_token(
    user_id: str,
    org_id: str,
    token_version: int = 1,
    auth_version: int = 1,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a cryptographically signed PyJWT refresh token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    sub_canonical = _validate_canonical_uuid(user_id, "user_id")
    org_canonical = _validate_canonical_uuid(org_id, "org_id")
    jti_canonical = str(uuid.uuid4()).lower()

    payload: Dict[str, Any] = {
        "sub": sub_canonical,
        "org_id": org_canonical,
        "token_version": int(token_version),
        "auth_version": int(auth_version),
        "type": "refresh",
        "jti": jti_canonical,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    token = jwt.encode(
        payload,
        settings.APP_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def decode_and_verify_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decode and strictly verify a JWT token.
    
    Verifies:
      - Valid signature using allowlisted algorithm
      - Expiration with zero leeway
      - Safe numeric bounds on timestamps
      - Asymmetric 30-second forward clock skew tolerance on iat/nbf
      - Canonical lowercase UUIDv4 for sub, org_id, jti
      - Expected token type matching
    """
    if not token or not isinstance(token, str):
        raise InvalidTokenError("Token must be a non-empty string")

    try:
        # Decode with explicit algorithm allowlist and zero leeway
        payload = jwt.decode(
            token,
            settings.APP_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={
                "verify_exp": True,
                "verify_iat": False,
                "verify_nbf": False,
                "require": ["exp", "iat", "nbf", "sub", "org_id", "jti", "type"],
            },
            leeway=0,
        )
    except jwt.ExpiredSignatureError:
        logger.warning("Token decoding failed: Signature has expired")
        raise InvalidTokenError("Token has expired")
    except jwt.InvalidAlgorithmError:
        logger.warning("Token decoding failed: Disallowed algorithm")
        raise InvalidTokenError("Invalid token algorithm")
    except jwt.PyJWTError as exc:
        logger.warning("Token decoding failed: %s", type(exc).__name__)
        raise InvalidTokenError(f"Token is invalid or malformed")

    # Verify token type
    token_type = payload.get("type")
    if token_type != expected_type:
        logger.warning("Token type mismatch: expected %s, got %s", expected_type, token_type)
        raise InvalidTokenError("Invalid token type")

    # Validate timestamps and forward clock skew
    now_ts = datetime.now(timezone.utc).timestamp()

    exp_ts = _validate_numeric_timestamp(payload.get("exp"), "exp")
    iat_ts = _validate_numeric_timestamp(payload.get("iat"), "iat")
    nbf_ts = _validate_numeric_timestamp(payload.get("nbf"), "nbf")

    if exp_ts <= now_ts:
        raise InvalidTokenError("Token has expired")

    # Forward clock skew tolerance: iat and nbf cannot be more than 30s in the future
    if iat_ts > now_ts + CLOCK_SKEW_TOLERANCE_SECONDS:
        logger.warning("Token iat is too far in future (possible clock desync or replay)")
        raise InvalidTokenError("Token iat exceeds clock skew tolerance")

    if nbf_ts > now_ts + CLOCK_SKEW_TOLERANCE_SECONDS:
        logger.warning("Token nbf is too far in future")
        raise InvalidTokenError("Token nbf exceeds clock skew tolerance")

    # Validate canonical lowercase UUIDs
    payload["sub"] = _validate_canonical_uuid(payload.get("sub"), "sub")
    payload["org_id"] = _validate_canonical_uuid(payload.get("org_id"), "org_id")
    payload["jti"] = _validate_canonical_uuid(payload.get("jti"), "jti")

    return payload
