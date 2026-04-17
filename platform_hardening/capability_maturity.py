from __future__ import annotations

from dataclasses import asdict, dataclass


class CapabilityContractError(ValueError):
    """Raised when a capability or lane request violates maturity contracts."""


FIRST_CLASS = "first_class"
BOUNDED_PROTOTYPE = "bounded_prototype"
STRUCTURAL_ONLY = "structural_only"
FUTURE = "future"


@dataclass(frozen=True)
class LaneMaturityContract:
    lane_id: str
    maturity: str
    app_types: list[str]
    allowed_frontends: list[str]
    capability_families: list[str]
    summary: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


LANE_CONTRACTS: dict[str, LaneMaturityContract] = {
    "first_class_commercial": LaneMaturityContract(
        lane_id="first_class_commercial",
        maturity=FIRST_CLASS,
        app_types=["internal_tool", "workspace_app", "saas_web_app", "api_service", "workflow_system", "copilot_chat_app"],
        allowed_frontends=["react_next"],
        capability_families=["commercial_web", "proof", "readiness", "reliability"],
        summary="Commercial web lane is first-class with deterministic build/ship/proof coverage.",
    ),
    "first_class_mobile": LaneMaturityContract(
        lane_id="first_class_mobile",
        maturity=FIRST_CLASS,
        app_types=["mobile_app"],
        allowed_frontends=["flutter_mobile"],
        capability_families=["mobile_generation", "proof", "readiness"],
        summary="Mobile lane is first-class for deterministic Flutter+backend generation with auth-ready, state, navigation, and offline scaffolds.",
    ),
    "first_class_game": LaneMaturityContract(
        lane_id="first_class_game",
        maturity=FIRST_CLASS,
        app_types=["game_app"],
        allowed_frontends=["godot_game"],
        capability_families=["game_generation", "proof", "readiness"],
        summary="Game lane is first-class for deterministic Godot project scaffolds with bounded gameplay/runtime contracts and explicit operator extension boundaries.",
    ),
    "first_class_realtime": LaneMaturityContract(
        lane_id="first_class_realtime",
        maturity=FIRST_CLASS,
        app_types=["realtime_system"],
        allowed_frontends=["react_next"],
        capability_families=["realtime_generation", "world_state_scaffold", "proof", "readiness"],
        summary="Realtime lane is first-class for deterministic stream/world-state generation with bounded websocket, alert/action, and connector scaffolds.",
    ),
    "first_class_enterprise_agent": LaneMaturityContract(
        lane_id="first_class_enterprise_agent",
        maturity=FIRST_CLASS,
        app_types=["enterprise_agent_system"],
        allowed_frontends=["react_next"],
        capability_families=["agent_workflow_scaffold", "approvals", "proof", "readiness"],
        summary="Enterprise-agent lane is first-class for deterministic multi-role workflow, approvals, memory, and briefing/reporting scaffolds under operator governance.",
    ),
}


CAPABILITY_FAMILY_MATURITY: dict[str, dict[str, object]] = {
    "chat-first": {
        "maturity": BOUNDED_PROTOTYPE,
        "supported": [
            "preview",
            "clarification",
            "default_inference",
            "project_memory",
            "conversation_to_spec",
            "structured_preview_contract",
            "unsupported_guidance",
        ],
        "unsupported": ["auto_ship_without_preview"],
        "summary": "Chat path is preview-first and deterministic, with explicit unsupported handling.",
    },
    "agent-runtime": {
        "maturity": BOUNDED_PROTOTYPE,
        "supported": [
            "task_modeling",
            "approval_gating",
            "blocked_semantics",
            "audit_log",
            "replay_signature",
            "bounded_execution_contract",
            "confidence_reporting",
        ],
        "unsupported": ["unbounded_desktop_control", "opaque_side_effect_execution"],
        "summary": "Agent runtime is bounded and approval-gated with deterministic replay metadata.",
    },
    "self-extension": {
        "maturity": BOUNDED_PROTOTYPE,
        "supported": [
            "sandbox_generation",
            "validation_thresholds",
            "registry_activation",
            "quarantine",
            "rollback_reference",
            "operator_visibility",
            "candidate_contracts",
        ],
        "unsupported": ["direct_core_mutation_without_approval"],
        "summary": "Self-extension remains sandbox-first; activation is gated by validation and approval policy.",
    },
    "multimodal-world-state": {
        "maturity": STRUCTURAL_ONLY,
        "supported": [
            "schema_normalization",
            "world_state_snapshot",
            "contract_metadata",
            "schema_consistency_validation",
        ],
        "unsupported": ["live_multimodal_execution"],
        "summary": "Multimodal/world-state support is schema-contract groundwork only.",
    },
    "security": {
        "maturity": BOUNDED_PROTOTYPE,
        "supported": [
            "auth_authz_pack",
            "rbac_scaffold",
            "abac_scaffold",
            "secrets_policy",
            "audit_defaults",
            "safe_generation_defaults",
            "policy_hooks",
        ],
        "unsupported": [
            "live_auth_provider_without_operator_credentials",
            "automated_penetration_testing",
        ],
        "summary": "Security foundations are bounded-prototype; auth provider credentials and live enforcement require operator integration.",
    },
    "commerce": {
        "maturity": BOUNDED_PROTOTYPE,
        "supported": [
            "plan_catalog",
            "subscription_model",
            "entitlement_model",
            "billing_webhooks",
            "billing_admin_surfaces",
            "stripe_adapter_scaffold",
        ],
        "unsupported": [
            "live_payment_processing_without_operator_credentials",
            "automated_tax_compliance",
        ],
        "summary": "Commerce layer is bounded-prototype; payment credentials and live billing enforcement require operator integration.",
    },
    "cross-lane-composition": {
        "maturity": BOUNDED_PROTOTYPE,
        "supported": [
            "app_plus_agent",
            "app_plus_realtime",
            "app_plus_mobile_companion",
            "app_plus_payment_layer",
            "composition_contract_validation",
            "composition_additive_output",
            "combined_semantics_contract",
        ],
        "unsupported": [
            "arbitrary_lane_mixing_without_contract",
            "maturity_tier_blurring",
        ],
        "summary": "Cross-lane composition is bounded-prototype; valid patterns are registered and contract-validated.",
    },
    "lifecycle": {
        "maturity": BOUNDED_PROTOTYPE,
        "supported": [
            "regen_safety_classification",
            "migration_aware_updates",
            "capability_evolution_tracking",
            "maintenance_semantics",
            "lifecycle_contract",
        ],
        "unsupported": [
            "automated_schema_diff_migration",
            "silent_destructive_overwrite",
        ],
        "summary": "Lifecycle/regeneration is bounded-prototype; migration execution requires operator CI integration.",
    },
    "enterprise-readiness": {
        "maturity": BOUNDED_PROTOTYPE,
        "supported": [
            "deployment_expectations",
            "supportability_contract",
            "operational_runbooks",
            "known_limitations_registry",
            "escalation_boundaries",
        ],
        "unsupported": [
            "automated_runbook_execution",
            "live_observability_backend",
        ],
        "summary": "Enterprise readiness artifacts are bounded-prototype scaffolds; execution requires operator infrastructure integration.",
    },
}


APP_TYPE_TO_LANE = {
    "mobile_app": "first_class_mobile",
    "game_app": "first_class_game",
    "realtime_system": "first_class_realtime",
    "enterprise_agent_system": "first_class_enterprise_agent",
}


def resolve_lane_contract(app_type: str) -> LaneMaturityContract:
    lane_id = APP_TYPE_TO_LANE.get(app_type, "first_class_commercial")
    contract = LANE_CONTRACTS.get(lane_id)
    if contract is None:
        raise CapabilityContractError(f"No lane contract registered for app_type '{app_type}'")
    return contract


def enforce_lane_contract(app_type: str, stack_selection: dict[str, str]) -> LaneMaturityContract:
    contract = resolve_lane_contract(app_type)
    if app_type not in contract.app_types:
        raise CapabilityContractError(
            f"app_type '{app_type}' is not permitted in lane '{contract.lane_id}'"
        )
    frontend = stack_selection.get("frontend", "")
    if frontend not in contract.allowed_frontends:
        allowed = ", ".join(sorted(contract.allowed_frontends))
        raise CapabilityContractError(
            f"Lane '{contract.lane_id}' only supports frontend stack(s): {allowed}. Requested: {frontend}"
        )
    return contract


def evaluate_capability_family(
    family: str,
    requested: list[str] | None = None,
) -> dict[str, object]:
    if family not in CAPABILITY_FAMILY_MATURITY:
        raise CapabilityContractError(f"Unknown capability family '{family}'")

    config = CAPABILITY_FAMILY_MATURITY[family]
    supported = set(str(item) for item in config.get("supported", []))
    unsupported = set(str(item) for item in config.get("unsupported", []))
    requested_items = [str(item) for item in (requested or [])]

    missing_supported = sorted(item for item in requested_items if item not in supported)
    explicitly_unsupported = sorted(item for item in requested_items if item in unsupported)

    return {
        "family": family,
        "maturity": config.get("maturity", BOUNDED_PROTOTYPE),
        "summary": config.get("summary", ""),
        "supported": sorted(supported),
        "unsupported": sorted(unsupported),
        "requested": requested_items,
        "unsupported_requested": sorted(set(missing_supported + explicitly_unsupported)),
        "accepted": not missing_supported and not explicitly_unsupported,
    }
