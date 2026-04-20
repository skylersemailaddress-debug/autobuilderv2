from __future__ import annotations

from security.auth.providers import validate_token
from security.authz.policy_engine import authorize
from commerce.entitlements.service import check_entitlement


def auth_middleware(token: str, action: str = "read", user: str | None = None, feature: str | None = None, approved: bool = False) -> bool:
    if not validate_token(token):
        return False
    authorize(action, {"allowed": True, "approved": approved})
    if user and feature:
        check_entitlement(user, feature)
    return True
