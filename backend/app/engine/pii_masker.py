"""PII masking — HMAC-based deduplication with last-4 display."""

import hashlib
import hmac
from app.config import settings


def _hmac_hash(value: str) -> str:
    """HMAC-SHA256 hash for deduplication without exposing raw PII."""
    return hmac.new(
        settings.pii_hmac_secret.encode(),
        value.encode(),
        hashlib.sha256,
    ).hexdigest()


def mask_value(value: str | None, show_last: int = 4) -> str:
    """Mask a PII value, showing only the last N characters."""
    if not value:
        return "****"
    if len(value) <= show_last:
        return "*" * len(value)
    return "*" * (len(value) - show_last) + value[-show_last:]


def hash_for_dedup(value: str | None) -> str | None:
    """Return HMAC hash for deduplication comparisons. None if no value."""
    if not value:
        return None
    return _hmac_hash(value.strip().lower())


def mask_employee_pii(employee_dict: dict) -> dict:
    """Mask PII fields in an employee dictionary for API responses."""
    masked = dict(employee_dict)
    for field in ("nin", "bvn", "bank_account"):
        if masked.get(field):
            masked[field] = mask_value(masked[field])
    return masked
