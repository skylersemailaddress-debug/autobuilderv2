from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ApprovalRule:
    action: str
    requires_approval: bool
    risk_tier: str
    reason: str


_DEFAULT_RULES: dict[str, ApprovalRule] = {
    "read": ApprovalRule("read", False, "low", "read-only action"),
    "inspect": ApprovalRule("inspect", False, "low", "inspection-only action"),
    "safe_mutation": ApprovalRule("safe_mutation", False, "moderate", "bounded safe mutation"),
    "destructive_mutation": ApprovalRule("destructive_mutation", True, "high", "destructive change"),
    "ship": ApprovalRule("ship", True, "high", "release-impacting action"),
    "restore": ApprovalRule("restore", True, "high", "state restoration action"),
    "self_extend": ApprovalRule("self_extend", True, "critical", "trust-elevating capability mutation"),
    "admin_override": ApprovalRule("admin_override", True, "critical", "administrative override"),
}


def resolve_rule(action: str, context: Mapping[str, Any] | None = None) -> ApprovalRule:
    context = context or {}
    if context.get("destructive") is True:
        return _DEFAULT_RULES["destructive_mutation"]
    return _DEFAULT_RULES.get(action, ApprovalRule(action, True, "high", "unrecognized action defaults to approval"))
