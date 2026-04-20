from __future__ import annotations

from typing import Dict, Set


class EntitlementError(Exception):
    pass


# simple in-memory entitlement store (replaceable with provider/db)
_ENTITLEMENTS: Dict[str, Set[str]] = {}


def grant_entitlement(user: str, feature: str) -> None:
    _ENTITLEMENTS.setdefault(user, set()).add(feature)


def revoke_entitlement(user: str, feature: str) -> None:
    if user in _ENTITLEMENTS:
        _ENTITLEMENTS[user].discard(feature)


def check_entitlement(user: str, feature: str) -> bool:
    if feature not in _ENTITLEMENTS.get(user, set()):
        raise EntitlementError(f"User '{user}' not entitled to '{feature}'")
    return True
