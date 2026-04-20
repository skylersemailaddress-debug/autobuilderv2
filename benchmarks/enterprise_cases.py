from __future__ import annotations

from typing import Mapping


REQUIRED_FIELDS = {"app_name", "stack", "status"}


def run_enterprise_case(case: Mapping[str, object] | None = None) -> bool:
    case = case or {}
    if not REQUIRED_FIELDS.issubset(set(case.keys())):
        return False
    if case.get("status") != "ready":
        return False
    return True
