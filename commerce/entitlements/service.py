from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Set


class EntitlementError(Exception):
    pass


_STORE_PATH = Path("commerce/entitlements/store.json")
_PLAN_FEATURES: Dict[str, Set[str]] = {
    "free": {"read"},
    "pro": {"read", "build", "deploy"},
    "enterprise": {"read", "build", "deploy", "admin", "self_extend"},
}


def _load_store() -> Dict[str, Set[str]]:
    if not _STORE_PATH.exists():
        return {}
    raw = json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    return {user: set(features) for user, features in raw.items()}


def _save_store(store: Dict[str, Set[str]]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    serializable = {user: sorted(features) for user, features in store.items()}
    _STORE_PATH.write_text(json.dumps(serializable, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def grant_entitlement(user: str, feature: str) -> None:
    store = _load_store()
    store.setdefault(user, set()).add(feature)
    _save_store(store)


def revoke_entitlement(user: str, feature: str) -> None:
    store = _load_store()
    if user in store:
        store[user].discard(feature)
        _save_store(store)


def grant_plan(user: str, plan: str) -> None:
    if plan not in _PLAN_FEATURES:
        raise EntitlementError(f"Unknown plan: {plan}")
    store = _load_store()
    store[user] = set(_PLAN_FEATURES[plan])
    _save_store(store)


def admin_override(user: str, feature: str, enabled: bool) -> None:
    if enabled:
        grant_entitlement(user, feature)
    else:
        revoke_entitlement(user, feature)


def check_entitlement(user: str, feature: str) -> bool:
    store = _load_store()
    if feature not in store.get(user, set()):
        raise EntitlementError(f"User '{user}' not entitled to '{feature}'")
    return True
