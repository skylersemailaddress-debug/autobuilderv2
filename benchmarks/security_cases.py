from __future__ import annotations

from typing import Mapping


def run_security_case(result: Mapping[str, object] | None = None) -> bool:
    result = result or {}
    # must explicitly prove no secrets leak and auth enforced
    if result.get("secrets_exposed"):
        return False
    if not result.get("auth_enforced"):
        return False
    return True
