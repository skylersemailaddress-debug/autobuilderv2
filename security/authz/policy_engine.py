from __future__ import annotations

from typing import Mapping


class AuthorizationError(Exception):
    pass


def authorize(action: str, context: Mapping[str, object] | None = None) -> bool:
    context = context or {}

    # deny-by-default
    if not context.get("allowed", False):
        raise AuthorizationError(f"Action '{action}' is not allowed by default policy")

    # explicit forbidden override
    if context.get("forbidden"):
        raise AuthorizationError(f"Action '{action}' explicitly forbidden")

    # require approval if flagged
    if context.get("requires_approval") and not context.get("approved"):
        raise AuthorizationError(f"Action '{action}' requires approval")

    return True
