from __future__ import annotations

import re

_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(secret\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(token\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(password\s*[=:]\s*)([^\s,;]+)"),
]


def redact(text: str) -> str:
    redacted = text
    for pattern in _PATTERNS:
        redacted = pattern.sub(r"\1****", redacted)
    return redacted
