from __future__ import annotations

from typing import Any, Mapping


def classify_mutation(target_path: str, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    destructive = bool(context.get("destructive", False))
    critical = target_path.startswith(("control_plane/", "policies/", ".github/", "security/", "execution/"))
    risk = "critical" if critical else ("high" if destructive else "moderate")
    return {
        "target_path": target_path,
        "destructive": destructive,
        "critical": critical,
        "risk_tier": risk,
    }
