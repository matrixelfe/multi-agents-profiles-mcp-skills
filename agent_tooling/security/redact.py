"""Secret redaction utilities. Never store or log PATs, API keys, or auth headers."""
from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEY_PATTERNS = re.compile(
    r"(api_?token|access_?token|refresh_?token|^token$|_token$|key|secret|password|auth|(?:^|_)pat(?:$|_)|credential|bearer)",
    re.IGNORECASE,
)


_INLINE_SECRET_PATTERNS = [
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{20,})\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{16,}\b", re.IGNORECASE),
]


def redact_text(text: str) -> str:
    """Redact common API keys, PATs, and Bearer tokens from free-form text."""
    out = str(text or "")
    for pat in _INLINE_SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def redact_dict(data: Any) -> Any:
    """Recursively redact sensitive keys in dicts/lists."""
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if SENSITIVE_KEY_PATTERNS.search(str(k)):
                out[k] = "[REDACTED]"
            else:
                out[k] = redact_dict(v)
        return out
    if isinstance(data, list):
        return [redact_dict(item) for item in data]
    return data
