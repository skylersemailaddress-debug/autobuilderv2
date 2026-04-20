from __future__ import annotations

from typing import Any, Mapping

from control_plane.decision_log import DecisionLog
from control_plane.approval_rules import resolve_rule


class ApprovalEngine:
    def __init__(self, decision_log: DecisionLog | None = None) -> None:
        self.decision_log = decision_log or DecisionLog()

    def evaluate(self, action: str, actor: str, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        rule = resolve_rule(action, context)
        approved = not rule.requires_approval or bool((context or {}).get("approved", False))
        result = self.decision_log.record(
            action=action,
            approved=approved,
            reason=rule.reason,
            actor=actor,
        )
        result["risk_tier"] = rule.risk_tier
        result["requires_approval"] = rule.requires_approval
        return result
