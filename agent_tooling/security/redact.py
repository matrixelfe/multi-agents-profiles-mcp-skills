"""Secret redaction utilities. Never store or log PATs, API keys, or auth headers."""
from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEY_PATTERNS = re.compile(
    r"(api_?token|access_?token|refresh_?token|^token$|_token$|key|secret|password|auth|(?:^|_)pat(?:$|_)|credential|bearer)",
    re.IGNORECASE,
)


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
