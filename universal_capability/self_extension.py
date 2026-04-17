from __future__ import annotations

from pathlib import Path

from platform_hardening.packs import get_pack_registry
from universal_capability.failure_intelligence import (
    append_capability_failure,
    emit_capability_replay_case,
    summarize_capability_confidence,
)
from universal_capability.governance import evaluate_registration, register_or_quarantine_candidate
from universal_capability.tool_factory import generate_tool_candidate, validate_tool_candidate


def detect_capability_gaps(*, lane_id: str, requested_capabilities: list[str]) -> list[str]:
    pack_profile = get_pack_registry().compose_lane_profile(lane_id)
    existing = set()
    for pack in pack_profile.get("packs", []):
        if isinstance(pack, dict):
            for cap in pack.get("capabilities", []):
                existing.add(str(cap))

    return sorted({cap for cap in requested_capabilities if cap not in existing})


def _tool_type_for_gap(gap: str) -> str:
    text = gap.lower()
    if "validate" in text or "check" in text:
        return "validator"
    if "connect" in text or "sensor" in text or "stream" in text:
        return "connector"
    if "helper" in text or "utility" in text:
        return "helper"
    return "domain_utility"


def _enforce_sandbox_boundary(path: str) -> str:
    resolved = Path(path).resolve()
    parts = set(resolved.parts)
    if ".git" in parts:
        raise ValueError("sandbox_root cannot point inside .git")
    return str(resolved)


def synthesize_missing_capabilities(
    *,
    lane_id: str,
    requested_capabilities: list[str],
    sandbox_root: str,
    registry_path: str,
    quarantine_path: str,
    require_approval_for_core: bool,
    approved: bool,
    failure_intelligence_root: str,
) -> dict[str, object]:
    sandbox_root = _enforce_sandbox_boundary(sandbox_root)
    missing = detect_capability_gaps(lane_id=lane_id, requested_capabilities=requested_capabilities)

    generated: list[dict[str, object]] = []
    registered: list[str] = []
    quarantined: list[str] = []
    failure_intelligence: list[dict[str, object]] = []

    for gap in missing:
        candidate = generate_tool_candidate(
            sandbox_root=sandbox_root,
            tool_name=gap,
            tool_type=_tool_type_for_gap(gap),
            purpose=f"fill capability gap: {gap}",
            lane_id=lane_id,
        )
        validation = validate_tool_candidate(candidate)
        decision = evaluate_registration(
            candidate=candidate,
            validation_report=validation,
            require_approval_for_core=require_approval_for_core,
            approved=approved,
        )
        registration = register_or_quarantine_candidate(
            registry_path=registry_path,
            quarantine_path=quarantine_path,
            candidate=candidate,
            decision=decision,
        )

        generated.append(
            {
                "gap": gap,
                "candidate": candidate,
                "validation": validation,
                "decision": decision,
                "registration": registration,
            }
        )
        if registration["status"] == "registered":
            registered.append(str(candidate.get("tool_id", "")))
        if registration["status"] == "quarantined":
            quarantined.append(str(candidate.get("tool_id", "")))
            failure_entry = append_capability_failure(
                target_root=failure_intelligence_root,
                capability_id=str(candidate.get("tool_id", "")),
                stage="registration",
                error_message=str(decision.get("rejection_reason", "quarantined")),
                replay_inputs={
                    "candidate": candidate,
                    "validation": validation,
                },
            )
            replay_case = emit_capability_replay_case(
                target_root=failure_intelligence_root,
                capability_id=str(candidate.get("tool_id", "")),
                replay_inputs={
                    "candidate_signature_sha256": candidate.get("candidate_signature_sha256", ""),
                    "validation": validation,
                    "decision": decision,
                },
            )
            failure_intelligence.append(
                {
                    "tool_id": str(candidate.get("tool_id", "")),
                    "failure_entry": failure_entry,
                    "replay_case": replay_case,
                }
            )

    if not missing:
        status = "no_gap"
    elif registered and not quarantined:
        status = "extended"
    elif quarantined and not registered:
        status = "quarantined_only"
    else:
        status = "partially_extended"

    return {
        "lane_id": lane_id,
        "sandbox_root": sandbox_root,
        "requested_capabilities": sorted(set(requested_capabilities)),
        "missing_capabilities": missing,
        "generated": generated,
        "registered_tool_ids": sorted(registered),
        "quarantined_tool_ids": sorted(quarantined),
        "activation_summary": {
            "registered_count": len(registered),
            "quarantined_count": len(quarantined),
            "rollback_references": [f"rollback::{tool_id}" for tool_id in sorted(registered)],
        },
        "failure_intelligence": failure_intelligence,
        "confidence_summary": summarize_capability_confidence(target_root=failure_intelligence_root),
        "status": status,
    }
