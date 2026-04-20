from __future__ import annotations

import hmac
import os
from typing import Iterable


def _allowed_tokens() -> list[str]:
    raw = os.getenv("AUTOBUILDER_ALLOWED_TOKENS", "")
    tokens = [t.strip() for t in raw.split(",") if t.strip()]
    if not tokens:
        tokens = ["dev-token"]
    return tokens


def validate_token(token: str, allowed_tokens: Iterable[str] | None = None) -> bool:
    if not token or not isinstance(token, str):
        return False
    candidates = list(allowed_tokens) if allowed_tokens is not None else _allowed_tokens()
    return any(hmac.compare_digest(token, candidate) for candidate in candidates)
