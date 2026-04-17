from __future__ import annotations

"""Cross-lane composition groundwork.

Defines valid multi-lane capability combinations, composition contracts,
and validation rules for builds that span multiple capability families.
Preserves first-class lane discipline — composition does not blur
maturity tiers.
"""

import hashlib
import json
from pathlib import Path

from platform_hardening.capability_maturity import (
    BOUNDED_PROTOTYPE,
    FIRST_CLASS,
    STRUCTURAL_ONLY,
    CapabilityContractError,
    LANE_CONTRACTS,
)


# ---------------------------------------------------------------------------
# Composition patterns — validated multi-lane/family combos
# ---------------------------------------------------------------------------

VALID_COMPOSITION_PATTERNS: dict[str, dict[str, object]] = {
    "app_plus_agent": {
        "pattern_id": "app_plus_agent",
        "primary_lane": "first_class_commercial",
        "secondary_capability": "agent-runtime",
        "maturity": BOUNDED_PROTOTYPE,
        "summary": "Commercial web app with bounded agent workflow scaffold.",
        "composition_rules": [
            "primary_lane_must_be_first_class",
            "agent_capability_gated_by_approval",
            "agent_scope_bounded_to_app_domain",
        ],
        "unsupported": ["unbounded_agent_outside_app_domain"],
    },
    "app_plus_realtime": {
        "pattern_id": "app_plus_realtime",
        "primary_lane": "first_class_commercial",
        "secondary_lane": "first_class_realtime",
        "maturity": FIRST_CLASS,
        "summary": "Commercial app with realtime stream integration — both lanes are first-class.",
        "composition_rules": [
            "both_lanes_must_be_first_class",
            "realtime_scope_defined_in_ir",
            "world_state_contract_required",
        ],
        "unsupported": [],
    },
    "app_plus_mobile_companion": {
        "pattern_id": "app_plus_mobile_companion",
        "primary_lane": "first_class_commercial",
        "secondary_lane": "first_class_mobile",
        "maturity": BOUNDED_PROTOTYPE,
        "summary": "Commercial web app with mobile companion app — bounded prototype for cross-lane coordination.",
        "composition_rules": [
            "shared_api_contract_required",
            "auth_model_must_be_consistent_across_lanes",
            "offline_sync_strategy_required",
        ],
        "unsupported": ["single_codebase_cross_platform_without_explicit_ir"],
    },
    "app_plus_payment_layer": {
        "pattern_id": "app_plus_payment_layer",
        "primary_lane": "first_class_commercial",
        "secondary_capability": "commerce",
        "maturity": BOUNDED_PROTOTYPE,
        "summary": "Commercial app with payment/subscription layer — scaffolded with operator-supplied provider.",
        "composition_rules": [
            "billing_webhook_signature_verification_required",
            "entitlement_check_required_on_gated_routes",
            "no_plaintext_payment_credentials",
        ],
        "unsupported": ["live_payment_processing_without_operator_credentials"],
    },
}


class CompositionContractError(ValueError):
    """Raised when a requested composition pattern violates contract rules."""


def resolve_composition_contract(pattern_id: str) -> dict[str, object]:
    """Return the composition contract for a given pattern.

    Raises CompositionContractError if the pattern is unknown.
    """
    pattern = VALID_COMPOSITION_PATTERNS.get(pattern_id)
    if pattern is None:
        known = sorted(VALID_COMPOSITION_PATTERNS)
        raise CompositionContractError(
            f"Unknown composition pattern '{pattern_id}'. Known: {known}"
        )
    return dict(pattern)


def evaluate_composition_request(
    primary_lane: str,
    secondary: str,
) -> dict[str, object]:
    """Evaluate whether a primary-lane + secondary-lane/capability combination is supported.

    Returns an evaluation dict with `accepted`, `pattern`, and any `violations`.
    """
    violations: list[str] = []

    # Primary must be a registered lane
    if primary_lane not in LANE_CONTRACTS:
        violations.append(f"primary_lane '{primary_lane}' is not a registered lane contract")

    # Find matching pattern
    matched_patterns = [
        p for p in VALID_COMPOSITION_PATTERNS.values()
        if p.get("primary_lane") == primary_lane
        and (p.get("secondary_lane") == secondary or p.get("secondary_capability") == secondary)
    ]

    if not matched_patterns:
        violations.append(
            f"No valid composition pattern for primary_lane='{primary_lane}' + secondary='{secondary}'"
        )
        return {
            "accepted": False,
            "pattern": None,
            "violations": violations,
            "maturity": None,
        }

    pattern = matched_patterns[0]
    primary_contract = LANE_CONTRACTS.get(primary_lane)
    if primary_contract and primary_contract.maturity != FIRST_CLASS:
        violations.append(f"primary_lane '{primary_lane}' is not first_class — composition requires first_class primary")

    return {
        "accepted": len(violations) == 0,
        "pattern": pattern,
        "violations": violations,
        "maturity": pattern.get("maturity"),
    }


def list_valid_composition_patterns() -> list[dict[str, object]]:
    """Return all registered valid composition patterns."""
    return [dict(p) for p in VALID_COMPOSITION_PATTERNS.values()]


def _signature(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _overlay_for_pattern(pattern_id: str) -> dict[str, object]:
    if pattern_id == "app_plus_payment_layer":
        return {
            "files": [
                "composition/payment/billing_adapter.json",
                "composition/payment/entitlements.json",
                "composition/payment/webhook_policy.json",
            ],
            "additive_capabilities": ["billing_webhooks", "entitlement_checks", "plan_catalog_overlay"],
            "combined_semantics": {
                "proof": {"required": ["billing_webhook_signature_verification", "entitlement_path_proven"]},
                "readiness": {"required": ["operator_billing_runbook", "credential_boundary_declared"]},
                "validation": {"required": ["billing_routes_present", "no_plaintext_payment_credentials"]},
            },
        }
    if pattern_id == "app_plus_agent":
        return {
            "files": [
                "composition/agent/task_runtime_contract.json",
                "composition/agent/operator_controls.json",
                "composition/agent/approval_gates.json",
            ],
            "additive_capabilities": ["agent_task_runtime", "operator_approval_controls", "replay_audit_overlay"],
            "combined_semantics": {
                "proof": {"required": ["approval_gate_contract", "agent_replay_signature"]},
                "readiness": {"required": ["operator_gate_policy", "bounded_scope_statement"]},
                "validation": {"required": ["approval_required_for_sensitive_actions", "blocked_semantics_consistent"]},
            },
        }
    if pattern_id == "app_plus_realtime":
        return {
            "files": [
                "composition/realtime/channel_contract.json",
                "composition/realtime/world_state_mapping.json",
                "composition/realtime/alert_action_path.json",
            ],
            "additive_capabilities": ["event_channels", "world_state_projection", "alert_action_flow"],
            "combined_semantics": {
                "proof": {"required": ["world_state_contract_present", "event_channel_integrity"]},
                "readiness": {"required": ["realtime_operator_surface", "event_throughput_expectation"]},
                "validation": {"required": ["channel_markers_present", "event_to_action_path_present"]},
            },
        }
    raise CompositionContractError(f"No additive output contract for pattern '{pattern_id}'")


def generate_composition_output(
    *,
    primary_lane: str,
    secondary: str,
    target_root: str | Path,
) -> dict[str, object]:
    evaluation = evaluate_composition_request(primary_lane, secondary)
    if not evaluation.get("accepted", False):
        raise CompositionContractError("; ".join(evaluation.get("violations", [])))

    pattern = dict(evaluation.get("pattern") or {})
    pattern_id = str(pattern.get("pattern_id", ""))
    overlay = _overlay_for_pattern(pattern_id)

    root = Path(target_root).resolve()
    written_files: list[str] = []
    for relative in overlay["files"]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "composition_version": "v1",
            "pattern_id": pattern_id,
            "primary_lane": primary_lane,
            "secondary": secondary,
            "relative_path": relative,
            "bounded_honesty": "no_claim_beyond_registered_pattern_contract",
        }
        payload["payload_signature_sha256"] = _signature(payload)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written_files.append(str(path))

    machine_semantics = {
        "pattern_id": pattern_id,
        "proof": overlay["combined_semantics"]["proof"],
        "readiness": overlay["combined_semantics"]["readiness"],
        "validation": overlay["combined_semantics"]["validation"],
        "additive_capabilities": sorted(overlay["additive_capabilities"]),
    }
    machine_semantics["combined_signature_sha256"] = _signature(machine_semantics)

    summary_path = root / "composition" / f"{pattern_id}_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(machine_semantics, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "accepted": True,
        "pattern": pattern,
        "written_files": sorted(written_files + [str(summary_path)]),
        "machine_semantics": machine_semantics,
    }
