"""RFC 5321/5322 compliant regex and email validation utility.

Guarantees clean group transitions without malformed escape sequences.
"""

import re
from typing import Tuple

# Exact pattern transitions: must contain "](?:" and NEVER contain "]" + chr(92) + "(?:"
LOCAL_PART_REGEX = re.compile(
    r"^(?!.*\.\.)[a-zA-Z0-9_%+-](?:[a-zA-Z0-9._%+-]{0,62}[a-zA-Z0-9_%+-])?$"
)

DOMAIN_LABEL_REGEX = re.compile(
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
)

REQUIRED_SEQUENCE = "](?:"
FORBIDDEN_SEQUENCE = "]" + chr(92) + "(?:"

# Invariant assertions to guarantee pattern integrity at import time
assert REQUIRED_SEQUENCE in LOCAL_PART_REGEX.pattern, "LOCAL_PART_REGEX must contain clean group transition"
assert REQUIRED_SEQUENCE in DOMAIN_LABEL_REGEX.pattern, "DOMAIN_LABEL_REGEX must contain clean group transition"
assert FORBIDDEN_SEQUENCE not in LOCAL_PART_REGEX.pattern, "LOCAL_PART_REGEX must not contain malformed backslash"
assert FORBIDDEN_SEQUENCE not in DOMAIN_LABEL_REGEX.pattern, "DOMAIN_LABEL_REGEX must not contain malformed backslash"


def validate_email_format(email: str) -> Tuple[bool, str]:
    """Validate email address format strictly.
    
    Returns:
        (is_valid, normalized_email_or_error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string"

    email = email.strip()
    if len(email) > 254:
        return False, "Email exceeds maximum length of 254 characters"

    if "@" not in email:
        return False, "Email must contain an '@' separator"

    parts = email.split("@")
    if len(parts) != 2:
        return False, "Email must contain exactly one '@' separator"

    local_part, domain_part = parts

    if not local_part or len(local_part) > 64:
        return False, "Email local part must be between 1 and 64 characters"

    if not LOCAL_PART_REGEX.match(local_part):
        return False, "Email local part contains invalid characters or consecutive dots"

    if not domain_part or len(domain_part) > 253:
        return False, "Email domain part must be between 1 and 253 characters"

    labels = domain_part.split(".")
    if len(labels) < 2:
        return False, "Email domain must contain at least one dot separating labels"

    for label in labels:
        if not label or len(label) > 63:
            return False, "Email domain label must be between 1 and 63 characters"
        if not DOMAIN_LABEL_REGEX.match(label):
            return False, f"Domain label '{label}' is invalid"

    tld = labels[-1]
    if len(tld) < 2 or not tld.isalpha():
        return False, "Top-level domain must be alphabetic and at least 2 characters long"

    return True, f"{local_part}@{domain_part.lower()}"
