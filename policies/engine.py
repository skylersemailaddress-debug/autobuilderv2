from __future__ import annotations

from typing import Any, Mapping


class PolicyEngine:
    def evaluate(self, action: str, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        if context.get("forbidden"):
            return {"decision": "deny", "reason": "forbidden context"}
        if context.get("requires_approval"):
            return {"decision": "approve_required", "reason": "policy requires approval"}
        return {"decision": "allow", "reason": "default allow"}
