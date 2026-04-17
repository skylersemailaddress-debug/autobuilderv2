from __future__ import annotations

"""Cross-lane composition groundwork.

Defines valid multi-lane capability combinations, composition contracts,
and validation rules for builds that span multiple capability families.
Preserves first-class lane discipline — composition does not blur
maturity tiers.
"""

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
