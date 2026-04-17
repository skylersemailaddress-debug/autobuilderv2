from __future__ import annotations

import json
from pathlib import Path


def _load_registry(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"capabilities": [], "history": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_registry(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def evaluate_registration(
    *,
    candidate: dict[str, object],
    validation_report: dict[str, object],
    require_approval_for_core: bool,
    approved: bool,
) -> dict[str, object]:
    quality_threshold = int(candidate.get("quality_threshold", 80))
    quality = int(validation_report.get("quality_score", 0))
    is_valid = bool(validation_report.get("is_valid", False))

    core_impact = "core" in str(candidate.get("purpose", "")).lower()
    needs_approval = bool(require_approval_for_core and core_impact)
    approval_ok = (not needs_approval) or approved

    accepted = bool(is_valid and quality >= quality_threshold and approval_ok)
    rejection_reason = ""
    if not is_valid:
        rejection_reason = "candidate validation failed"
    elif quality < quality_threshold:
        rejection_reason = "quality below threshold"
    elif needs_approval and not approved:
        rejection_reason = "approval required for core-impact candidate"

    return {
        "accepted": accepted,
        "needs_approval": needs_approval,
        "rejection_reason": rejection_reason,
        "quality_threshold": quality_threshold,
        "quality_score": quality,
        "activation_status": "active" if accepted else "quarantined",
    }


def register_or_quarantine_candidate(
    *,
    registry_path: str | Path,
    quarantine_path: str | Path,
    candidate: dict[str, object],
    decision: dict[str, object],
) -> dict[str, object]:
    registry_file = Path(registry_path).resolve()
    quarantine_file = Path(quarantine_path).resolve()

    registry = _load_registry(registry_file)
    capabilities = registry.setdefault("capabilities", [])
    history = registry.setdefault("history", [])

    if decision.get("accepted", False):
        entry = {
            "tool_id": candidate.get("tool_id", ""),
            "status": "active",
            "activation": {
                "activation_status": "active",
                "quality_score": decision.get("quality_score"),
                "quality_threshold": decision.get("quality_threshold"),
            },
            "candidate": candidate,
        }
        capabilities.append(entry)
        history.append(
            {
                "event": "registered",
                "tool_id": candidate.get("tool_id", ""),
                "activation_status": "active",
            }
        )
        _save_registry(registry_file, registry)
        return {
            "status": "registered",
            "tool_id": candidate.get("tool_id", ""),
            "registry_path": str(registry_file),
        }

    quarantine_file.parent.mkdir(parents=True, exist_ok=True)
    payload = []
    if quarantine_file.exists():
        payload = json.loads(quarantine_file.read_text(encoding="utf-8"))
    payload.append(
        {
            "tool_id": candidate.get("tool_id", ""),
            "candidate": candidate,
            "reason": decision.get("rejection_reason", "rejected"),
            "activation_status": "quarantined",
            "quality_threshold": decision.get("quality_threshold"),
            "quality_score": decision.get("quality_score"),
        }
    )
    quarantine_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    history.append(
        {
            "event": "quarantined",
            "tool_id": candidate.get("tool_id", ""),
            "activation_status": "quarantined",
            "reason": decision.get("rejection_reason", "rejected"),
        }
    )
    _save_registry(registry_file, registry)
    return {
        "status": "quarantined",
        "tool_id": candidate.get("tool_id", ""),
        "quarantine_path": str(quarantine_file),
    }


def rollback_capability(*, registry_path: str | Path, tool_id: str) -> dict[str, object]:
    registry_file = Path(registry_path).resolve()
    registry = _load_registry(registry_file)
    changed = False
    for entry in registry.get("capabilities", []):
        if isinstance(entry, dict) and entry.get("tool_id") == tool_id and entry.get("status") == "active":
            entry["status"] = "rolled_back"
            changed = True
    registry.setdefault("history", []).append({"event": "rolled_back", "tool_id": tool_id})
    _save_registry(registry_file, registry)
    return {
        "status": "rolled_back" if changed else "not_found",
        "tool_id": tool_id,
        "registry_path": str(registry_file),
    }
