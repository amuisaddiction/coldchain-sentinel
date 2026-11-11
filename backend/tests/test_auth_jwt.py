"""Tests for security utilities, regex integrity, and PyJWT token lifecycle."""

import uuid
import time
from datetime import datetime, timezone, timedelta
import pytest
import jwt

from app.core.config import settings
from app.core.regex import (
    LOCAL_PART_REGEX,
    DOMAIN_LABEL_REGEX,
    validate_email_format,
    REQUIRED_SEQUENCE,
    FORBIDDEN_SEQUENCE,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_and_verify_token,
    InvalidTokenError,
)


def test_regex_invariants_and_literals():
    """Verify exact pattern literals, sequences, and compile states."""
    # Exact sequence checks
    assert REQUIRED_SEQUENCE in LOCAL_PART_REGEX.pattern
    assert REQUIRED_SEQUENCE in DOMAIN_LABEL_REGEX.pattern
    assert FORBIDDEN_SEQUENCE not in LOCAL_PART_REGEX.pattern
    assert FORBIDDEN_SEQUENCE not in DOMAIN_LABEL_REGEX.pattern

    # Pattern repr check
    assert "](?:" in repr(LOCAL_PART_REGEX.pattern)
    assert "](?:" in repr(DOMAIN_LABEL_REGEX.pattern)
    assert "]" + chr(92) + "(?:" not in repr(LOCAL_PART_REGEX.pattern)
    assert "]" + chr(92) + "(?:" not in repr(DOMAIN_LABEL_REGEX.pattern)


def test_regex_matching_and_rejections():
    """Verify email local-part and domain rules including boundary conditions."""
    # Valid emails
    valid_samples = [
        "user@example.com",
        "user.name@example.com",
        "user+tag@example.com",
        "user_name@example.com",
        "u@example.com",
        "user@ex-ample.com",
        "user@sub.example.com",
        "admin@coldchain.sentinel.org",
    ]
    for email in valid_samples:
        is_valid, norm = validate_email_format(email)
        assert is_valid is True, f"Expected {email} to be valid, got error: {norm}"

    # Invalid emails
    invalid_samples = [
        "user..name@example.com",  # Consecutive dots
        ".user@example.com",       # Leading dot
        "user.@example.com",       # Trailing dot
        "user@example..com",       # Consecutive domain dots
        "user@-example.com",       # Leading hyphen in domain
        "user@example-.com",       # Trailing hyphen in domain
        "user@example",            # Missing TLD
        "user@example.c",          # TLD too short (<2 chars)
        "user@example.123",        # Numeric TLD
        "@example.com",            # Missing local part
        "user@",                   # Missing domain
        "",                        # Empty
        "   ",                     # Whitespace only
    ]
    for email in invalid_samples:
        is_valid, _ = validate_email_format(email)
        assert is_valid is False, f"Expected {email} to be rejected"


def test_bcrypt_hashing_and_verification():
    """Verify bcrypt salt rounds, verification, and negative checks."""
    pwd = "CorrectHorseBatteryStaple123!"
    hashed = hash_password(pwd)
    assert hashed.startswith("$2b$12$")
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong-password", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_generation_and_valid_decoding():
    """Verify access and refresh token creation and parsing."""
    user_id = str(uuid.uuid4()).lower()
    org_id = str(uuid.uuid4()).lower()

    # Access token
    token = create_access_token(
        user_id=user_id,
        org_id=org_id,
        role="ADMIN",
        token_version=1,
        auth_version=1,
    )
    claims = decode_and_verify_token(token, expected_type="access")
    assert claims["sub"] == user_id
    assert claims["org_id"] == org_id
    assert claims["role"] == "ADMIN"
    assert claims["token_version"] == 1
    assert claims["auth_version"] == 1
    assert claims["type"] == "access"

    # Refresh token
    rtoken = create_refresh_token(
        user_id=user_id,
        org_id=org_id,
        token_version=1,
        auth_version=1,
    )
    rclaims = decode_and_verify_token(rtoken, expected_type="refresh")
    assert rclaims["sub"] == user_id
    assert rclaims["org_id"] == org_id
    assert rclaims["type"] == "refresh"


def test_jwt_tampered_and_malformed():
    """Verify tampered signature and malformed string rejection."""
    user_id = str(uuid.uuid4()).lower()
    org_id = str(uuid.uuid4()).lower()
    token = create_access_token(user_id=user_id, org_id=org_id, role="OPERATOR")

    # Tampered signature
    tampered = token[:-5] + ("AAAAA" if not token.endswith("AAAAA") else "BBBBB")
    with pytest.raises(InvalidTokenError):
        decode_and_verify_token(tampered)

    # Empty or malformed string
    with pytest.raises(InvalidTokenError):
        decode_and_verify_token("not.a.valid.jwt")
    with pytest.raises(InvalidTokenError):
        decode_and_verify_token("")


def test_jwt_expired_token_rejection():
    """Verify expired token rejection with zero leeway."""
    user_id = str(uuid.uuid4()).lower()
    org_id = str(uuid.uuid4()).lower()
    expired_token = create_access_token(
        user_id=user_id,
        org_id=org_id,
        role="OPERATOR",
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(InvalidTokenError):
        decode_and_verify_token(expired_token)


def test_jwt_wrong_algorithm_rejection():
    """Verify algorithm confusion / disallowed algorithm rejection."""
    payload = {
        "sub": str(uuid.uuid4()).lower(),
        "org_id": str(uuid.uuid4()).lower(),
        "role": "ADMIN",
        "token_version": 1,
        "auth_version": 1,
        "type": "access",
        "jti": str(uuid.uuid4()).lower(),
        "iat": int(time.time()),
        "nbf": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    # Unsigned token with none algorithm
    none_token = jwt.encode(payload, key="", algorithm="none")
    with pytest.raises(InvalidTokenError):
        decode_and_verify_token(none_token)


def test_jwt_forward_clock_skew():
    """Verify 30-second forward clock skew boundary conditions."""
    user_id = str(uuid.uuid4()).lower()
    org_id = str(uuid.uuid4()).lower()
    now_ts = int(time.time())

    # Token with iat 20 seconds in future (within 30s tolerance)
    payload_ok = {
        "sub": user_id,
        "org_id": org_id,
        "role": "ADMIN",
        "token_version": 1,
        "auth_version": 1,
        "type": "access",
        "jti": str(uuid.uuid4()).lower(),
        "iat": now_ts + 20,
        "nbf": now_ts + 20,
        "exp": now_ts + 3600,
    }
    token_ok = jwt.encode(payload_ok, settings.APP_SECRET_KEY, algorithm="HS256")
    claims = decode_and_verify_token(token_ok)
    assert claims["sub"] == user_id

    # Token with iat 45 seconds in future (exceeds 30s tolerance)
    payload_bad = {
        "sub": user_id,
        "org_id": org_id,
        "role": "ADMIN",
        "token_version": 1,
        "auth_version": 1,
        "type": "access",
        "jti": str(uuid.uuid4()).lower(),
        "iat": now_ts + 45,
        "nbf": now_ts + 45,
        "exp": now_ts + 3600,
    }
    token_bad = jwt.encode(payload_bad, settings.APP_SECRET_KEY, algorithm="HS256")
    with pytest.raises(InvalidTokenError):
        decode_and_verify_token(token_bad)


def test_jwt_canonical_uuid_enforcement():
    """Verify uppercase UUID is rejected and canonical lowercase is required."""
    valid_uuid = str(uuid.uuid4()).lower()
    uppercase_uuid = valid_uuid.upper()
    now_ts = int(time.time())

    payload = {
        "sub": uppercase_uuid,
        "org_id": valid_uuid,
        "role": "ADMIN",
        "token_version": 1,
        "auth_version": 1,
        "type": "access",
        "jti": str(uuid.uuid4()).lower(),
        "iat": now_ts,
        "nbf": now_ts,
        "exp": now_ts + 3600,
    }
    token = jwt.encode(payload, settings.APP_SECRET_KEY, algorithm="HS256")
    with pytest.raises(InvalidTokenError):
        decode_and_verify_token(token)
