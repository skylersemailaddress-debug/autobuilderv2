from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    expected_outcome: Dict[str, Any]
    goal: str = ""
    kind: str = "mission"
    nexus_mode_enabled: bool = False
    requires_resume: bool = False
    auto_approve_on_resume: bool = False
    spec_path: str | None = None
    app_type: str | None = None
    stack_selection: dict[str, str] | None = None
    composition_secondary: str | None = None
    requested_capabilities: list[str] | None = None
    approve_core: bool = False


BENCHMARK_CASES: List[BenchmarkCase] = [
    BenchmarkCase(
        name="simple_low_risk_mission",
        goal="Build an autonomous execution plan",
        expected_outcome={
            "final_status": "complete",
            "approval_required": False,
        },
    ),
    BenchmarkCase(
        name="repair_retry_generated_app",
        expected_outcome={
            "validation_status": "passed",
            "minimum_repair_count": 1,
        },
        kind="repair_flow",
    ),
    BenchmarkCase(
        name="approval_required_dangerous_mission",
        goal="Delete production resources safely",
        expected_outcome={
            "final_status": "awaiting_approval",
            "approval_required": True,
        },
    ),
    BenchmarkCase(
        name="repo_targeted_mission",
        goal="Update repository config and improve test coverage",
        expected_outcome={
            "final_status": "complete",
            "repo_mode": True,
        },
    ),
    BenchmarkCase(
        name="nexus_mission_mode_run",
        goal="Build an autonomous execution plan in Nexus mode",
        expected_outcome={
            "final_status": "complete",
            "nexus_mode": True,
        },
        nexus_mode_enabled=True,
    ),
    BenchmarkCase(
        name="interrupted_resumable_mission",
        goal="Delete production resources safely",
        expected_outcome={
            "final_status": "complete",
            "approval_required": True,
            "resumed": True,
        },
        nexus_mode_enabled=True,
        requires_resume=True,
        auto_approve_on_resume=True,
    ),
    BenchmarkCase(
        name="first_class_ship_flow",
        expected_outcome={
            "build_status": "ok",
            "proof_status_prefix": "certified",
            "packaging_status": "ready",
        },
        kind="ship",
        spec_path="specs",
    ),
    BenchmarkCase(
        name="lane_mobile_ship_flow",
        expected_outcome={
            "build_status": "ok",
            "proof_status_prefix": "certified",
            "packaging_status": "ready",
        },
        kind="lane_ship",
        app_type="mobile_app",
        stack_selection={
            "frontend": "flutter_mobile",
            "backend": "fastapi",
            "database": "postgres",
            "deployment": "docker_compose",
        },
    ),
    BenchmarkCase(
        name="lane_realtime_ship_flow",
        expected_outcome={
            "build_status": "ok",
            "proof_status_prefix": "certified",
            "packaging_status": "ready",
        },
        kind="lane_ship",
        app_type="realtime_system",
        stack_selection={
            "frontend": "react_next",
            "backend": "fastapi",
            "database": "postgres",
            "deployment": "docker_compose",
        },
    ),
    BenchmarkCase(
        name="lane_enterprise_ship_flow",
        expected_outcome={
            "build_status": "ok",
            "proof_status_prefix": "certified",
            "packaging_status": "ready",
        },
        kind="lane_ship",
        app_type="enterprise_agent_system",
        stack_selection={
            "frontend": "react_next",
            "backend": "fastapi",
            "database": "postgres",
            "deployment": "docker_compose",
        },
    ),
    BenchmarkCase(
        name="chat_preview_flow",
        expected_outcome={
            "chat_status": "preview_ready",
        },
        kind="chat_flow",
        goal="Build a mobile app called Field Assistant with alerts and history",
    ),
    BenchmarkCase(
        name="chat_build_flow",
        expected_outcome={
            "chat_status": "built",
            "proof_status_prefix": "certified",
        },
        kind="chat_flow",
        goal="Build a realtime app called Ops Signal with telemetry streams and operator controls",
        auto_approve_on_resume=True,
    ),
    BenchmarkCase(
        name="composition_payment_layer_flow",
        expected_outcome={
            "composition_status": "accepted",
        },
        kind="composition_flow",
        composition_secondary="commerce",
    ),
    BenchmarkCase(
        name="composition_agent_layer_flow",
        expected_outcome={
            "composition_status": "accepted",
        },
        kind="composition_flow",
        composition_secondary="agent-runtime",
    ),
    BenchmarkCase(
        name="composition_realtime_layer_flow",
        expected_outcome={
            "composition_status": "accepted",
        },
        kind="composition_flow",
        composition_secondary="first_class_realtime",
    ),
    BenchmarkCase(
        name="lifecycle_regeneration_flow",
        expected_outcome={
            "lifecycle_status": "ready",
        },
        kind="lifecycle_flow",
    ),
    BenchmarkCase(
        name="self_extension_rejection_scenario",
        expected_outcome={
            "status": "quarantined_only",
            "registered": False,
        },
        kind="self_extend",
        requested_capabilities=["core_auth_guard"],
        approve_core=False,
    ),
    BenchmarkCase(
        name="unsupported_feature_rejection",
        expected_outcome={
            "error_contains": "Unsupported",
            "unsupported_handled": True,
        },
        kind="unsupported_build",
    ),
    BenchmarkCase(
        name="self_extension_validation_scenario",
        expected_outcome={
            "status": "extended",
            "registered": True,
        },
        kind="self_extend",
        requested_capabilities=["custom_validator_for_geo"],
        approve_core=True,
    ),
    # --- Mission orchestration suite ---
    BenchmarkCase(
        name="mission_capability_requirement_derivation",
        goal="Build a realtime monitoring app with auth and billing",
        expected_outcome={
            "final_status": "complete",
            "capability_requirements_present": True,
        },
        kind="mission",
        nexus_mode_enabled=True,
    ),
    BenchmarkCase(
        name="mission_plan_machine_readable",
        goal="Create a payment processing workflow with RBAC",
        expected_outcome={
            "final_status": "complete",
            "mission_plan_present": True,
        },
        kind="mission",
        nexus_mode_enabled=True,
    ),
    BenchmarkCase(
        name="mission_operator_summary_present",
        goal="Build an enterprise admin dashboard with audit logs",
        expected_outcome={
            "final_status": "complete",
            "operator_summary_present": True,
        },
        kind="mission",
        nexus_mode_enabled=True,
    ),
    BenchmarkCase(
        name="mission_interruption_recovery_semantics",
        goal="Migrate production database schema safely",
        expected_outcome={
            "final_status": "awaiting_approval",
            "approval_required": True,
            "interruption_recovery_supported": True,
        },
        kind="mission",
        nexus_mode_enabled=True,
    ),
    # --- Capability acquisition suite ---
    BenchmarkCase(
        name="capability_acquisition_adapter_generation",
        goal="Integrate with a third-party document processing API",
        expected_outcome={
            "final_status": "complete",
        },
        kind="mission",
        requested_capabilities=["document_processing_adapter"],
        nexus_mode_enabled=True,
    ),
    # --- Composition flows extended ---
    BenchmarkCase(
        name="composition_mobile_companion_flow",
        expected_outcome={
            "composition_status": "accepted",
        },
        kind="composition_flow",
        composition_secondary="first_class_mobile",
    ),
    # --- Lane-specific ship flows extended ---
    BenchmarkCase(
        name="lane_game_ship_flow",
        expected_outcome={
            "build_status": "ok",
            "proof_status_prefix": "certified",
            "packaging_status": "ready",
        },
        kind="lane_ship",
        app_type="game_app",
        stack_selection={
            "frontend": "godot_game",
            "backend": "fastapi",
            "database": "postgres",
            "deployment": "docker_compose",
        },
    ),
    # --- Domain-pack validation suite ---
    BenchmarkCase(
        name="domain_pack_operations_workflow_valid",
        goal="Build an operations workflow system with task assignments and approvals",
        expected_outcome={
            "final_status": "complete",
        },
        kind="mission",
        nexus_mode_enabled=True,
    ),
    BenchmarkCase(
        name="domain_pack_regulated_honesty",
        goal="Build a HIPAA-compliant regulated data management system",
        expected_outcome={
            "final_status": "complete",
        },
        kind="mission",
        nexus_mode_enabled=True,
    ),
    # --- Unsupported/refusal honesty suite ---
    BenchmarkCase(
        name="unsupported_live_hardware_refusal",
        expected_outcome={
            "error_contains": "Unsupported",
            "unsupported_handled": True,
        },
        kind="unsupported_build",
    ),
    # --- Repo-targeted mutation safety suite ---
    BenchmarkCase(
        name="repo_mutation_critical_file_checkpoint",
        goal="Update database schema migration files in existing repo",
        expected_outcome={
            "final_status": "complete",
        },
        kind="mission",
        nexus_mode_enabled=True,
    ),
    # --- Adapter registry suite ---
    BenchmarkCase(
        name="adapter_registry_lane_resolution",
        goal="Resolve adapters for first_class_realtime lane",
        expected_outcome={
            "final_status": "complete",
        },
        kind="mission",
        nexus_mode_enabled=True,
    ),
    # --- Benchmark proof coverage ---
    BenchmarkCase(
        name="benchmark_proof_artifact_present",
        expected_outcome={
            "build_status": "ok",
            "proof_status_prefix": "certified",
            "packaging_status": "ready",
        },
        kind="ship",
        spec_path="specs",
    ),
]
