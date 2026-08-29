"""Input validation — dangerous pattern detection for text inputs."""

import re

DANGEROUS_PATTERNS = [
    (
        r"(?i)(DROP\s+TABLE|DELETE\s+FROM|UPDATE\s+\w+\s+SET|ALTER\s+TABLE|;\s*--)",
        "sql_injection",
    ),
    (r"(<script|javascript:|onerror=|onload=|<iframe)", "xss"),
    (r"(\.\./|\.\.\\|%2e%2e)", "path_traversal"),
    (r"(__import__|eval\(|exec\(|os\.system|subprocess)", "code_injection"),
]


def validate_text_input(text: str) -> tuple[bool, list[str]]:
    """Check text for dangerous patterns. Returns (safe, list_of_threats)."""
    threats = []
    for pattern, threat_type in DANGEROUS_PATTERNS:
        if re.search(pattern, text):
            threats.append(threat_type)
    return len(threats) == 0, threats


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Basic string sanitization — strip and truncate."""
    return value.strip()[:max_length]
