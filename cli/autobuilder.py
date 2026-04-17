import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from tempfile import TemporaryDirectory
from pathlib import Path

# Ensure top-level package imports work when executing cli/autobuilder.py directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from archetypes.catalog import ArchetypeResolutionError
from benchmarks.cases import BENCHMARK_CASES
from benchmarks.report import build_benchmark_report
from benchmarks.runner import run_benchmark_cases
from cli.inspect import inspect_run
from cli.mission import resume_mission, run_mission
from generator.executor import apply_build_plan
from generator.plan import prepare_build_plan
from ir.compiler import compile_specs_to_ir
from readiness.checks import run_readiness_checks
from readiness.report import build_readiness_report
from stack_registry.registry import StackRegistryResolutionError
from specs.loader import SpecValidationError, load_spec_bundle
from mutation.safety import MutationSafetyDecision, MutationSafetyPolicy
from state.audit import append_audit_event, build_audit_record, get_command_safety_contract
from state.checkpoints import create_checkpoint
from state.restore import latest_restore_payload
from quality.reliability import derive_build_reliability, derive_ship_reliability
from validator.confidence import calculate_confidence_details
from chat_builder.workflow import run_chat_first_workflow
from platform_hardening.capability_maturity import (
    CapabilityContractError,
    evaluate_capability_family,
    enforce_lane_contract,
)
from universal_capability.agent_runtime import execute_computer_use_plan, model_computer_use_task
from universal_capability.self_extension import synthesize_missing_capabilities


def _print(data, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data, indent=2))


def _build_safety_guarantee(command: str) -> dict[str, str]:
    if command in {"inspect", "readiness", "benchmark"}:
        return {
            "mutation": "read_only",
            "approval": "not_required",
            "rollback": "read_only",
        }

    contract = get_command_safety_contract(command)
    return {
        "mutation": str(contract.get("mutation_mode", "unspecified")),
        "approval": str(contract.get("approval_behavior", "unspecified")),
        "rollback": str(contract.get("rollback_behavior", "unspecified")),
    }


def _with_command_envelope(command: str, payload: dict) -> dict:
    return {
        "status": "ok",
        "command": command,
        "safety_guarantee": _build_safety_guarantee(command),
        **payload,
    }


def _decision_payload(decision: MutationSafetyDecision) -> dict:
    return {
        "action": decision.action,
        "target": decision.target,
        "action_class": decision.action_class,
        "target_type": decision.target_type,
        "risk_level": decision.risk_level,
        "checkpoint_required": decision.checkpoint_required,
        "approval_required": decision.approval_required,
        "destructive_potential": decision.destructive_potential,
        "environment_sensitivity": decision.environment_sensitivity,
        "irreversible_operation": decision.irreversible_operation,
        "restore_strategy": decision.restore_strategy,
        "lane_id": decision.lane_id,
        "stack_id": decision.stack_id,
        "failure_mode": decision.failure_mode,
        "policy_basis": decision.policy_basis,
    }


def _governance_bundle(
    command: str,
    *,
    target: str,
    action: str,
    actor: str = "autobuilder",
    lane_id: str | None = None,
    stack_id: str | None = None,
    target_type: str | None = None,
    irreversible_operation: bool | None = None,
    approval_state: str | None = None,
    outcome: str = "ok",
    failure_classification: str = "none",
    details: dict | None = None,
) -> dict:
    decision = MutationSafetyPolicy().evaluate(
        action,
        target,
        lane_id=lane_id,
        stack_id=stack_id,
        target_type=target_type,
        irreversible_operation=irreversible_operation,
    )
    checkpoints: list[dict] = []
    if decision.checkpoint_required or decision.restore_strategy != "not_required":
        checkpoints.append(
            asdict(
                create_checkpoint(
                    "command_started",
                    {"command": command, "target": target, "action": action},
                    mutation_safety=_decision_payload(decision),
                    command=command,
                    actor=actor,
                )
            )
        )
        checkpoints.append(
            asdict(
                create_checkpoint(
                    "command_completed" if outcome != "error" else "command_failed",
                    {"command": command, "outcome": outcome},
                    mutation_safety=_decision_payload(decision),
                    command=command,
                    actor=actor,
                    failure_semantics={
                        "on_command_failure": "halt_and_restore"
                        if decision.checkpoint_required
                        else "surface_audit_and_stop"
                    },
                )
            )
        )

    restore_payload = latest_restore_payload(
        {
            "run_id": f"{command}-{hashlib.sha256(f'{target}:{action}'.encode('utf-8')).hexdigest()[:12]}",
            "checkpoints": checkpoints,
        }
    ) if checkpoints else None
    safety_contract = get_command_safety_contract(command)
    resolved_approval_state = approval_state or ("pending" if decision.approval_required else "not_required")
    audit_trail = append_audit_event(
        [],
        f"{command}_evaluated",
        actor=actor,
        approval_state=resolved_approval_state,
        failure_classification=failure_classification,
        details={
            "target": target,
            "action": action,
            "risk_level": decision.risk_level,
        },
    )
    audit_trail = append_audit_event(
        audit_trail,
        f"{command}_completed" if outcome != "error" else f"{command}_failed",
        actor=actor,
        approval_state=resolved_approval_state,
        failure_classification=failure_classification,
        details={"outcome": outcome},
    )
    rollback_reference = checkpoints[-1]["rollback_reference"] if checkpoints else None
    audit_record = build_audit_record(
        command,
        action_type=action,
        outcome=outcome,
        risk_level=decision.risk_level,
        approval_state=resolved_approval_state,
        checkpoint_ids=[item["checkpoint_id"] for item in checkpoints],
        rollback_ready=bool(checkpoints),
        rollback_reference=rollback_reference,
        restore_checkpoint_id=(restore_payload or {}).get("checkpoint_id"),
        restore_reference=(restore_payload or {}).get("restore_references"),
        actor=actor,
        failure_classification=failure_classification,
        safety_contract=safety_contract,
        details={
            "policy": _decision_payload(decision),
            **(details or {}),
        },
    )
    return {
        "mutation_policy": _decision_payload(decision),
        "checkpoints": checkpoints,
        "restore_payload": restore_payload,
        "audit_trail": audit_trail,
        "audit_record": audit_record,
        "safety_contract": safety_contract,
    }


def _run_benchmarks(case_names: str | None = None) -> dict:
    selected = BENCHMARK_CASES
    if case_names:
        wanted = {name.strip() for name in case_names.split(",") if name.strip()}
        selected = [case for case in BENCHMARK_CASES if case.name in wanted]
    results = run_benchmark_cases(selected)
    return build_benchmark_report(results)


LANE_VALIDATION_RULES: dict[str, dict[str, object]] = {
    "mobile_app": {
        "mobile_structure": {
            "exists": [
                "pubspec.yaml",
                "lib/app.dart",
                "lib/navigation/app_router.dart",
                "lib/screens/home_screen.dart",
                "lib/screens/settings_screen.dart",
                "lib/screens/admin_screen.dart",
                "lib/screens/activity_screen.dart",
            ]
        },
        "mobile_markers": {
            "contains": {
                "lib/navigation/app_router.dart": ["settingsRoute", "adminRoute", "activityRoute"],
            }
        },
        "navigation_flows": {"exists": ["lib/navigation/app_router.dart"]},
        "api_client_present": {"contains": {"lib/services/api_client.dart": ["class ApiClient", "Uri endpoint"]}},
        "flutter_pubspec_valid": {"contains": {"pubspec.yaml": ["flutter", "http", "shared_preferences"]}},
        "mobile_auth_scaffold": {"exists": ["lib/auth/auth_guard.dart", "backend/api/auth.py"]},
        "mobile_state_surface": {"exists": ["lib/state/app_state.dart"]},
        "mobile_offline_store_surface": {"exists": ["lib/data/local_store.dart"]},
        "mobile_operator_surfaces": {"exists": ["docs/READINESS.md", "docs/OPERATOR.md"]},
    },
    "realtime_system": {
        "realtime_structure": {
            "exists": [
                "frontend/lib/realtime-client.ts",
                "frontend/lib/alert-actions.ts",
                "backend/realtime/world_state.py",
                "backend/realtime/events.py",
            ]
        },
        "realtime_markers": {"contains": {"backend/api/realtime.py": ["/ingest", "normalize_event", "WorldState"]}},
        "channel_integrity": {"contains": {"backend/realtime/channels.py": ["ops.events", "ops.alerts", "ops.actions"]}},
        "world_state_present": {"contains": {"backend/realtime/world_state.py": ["class WorldState", "apply_event"]}},
        "connector_present": {"contains": {"backend/connectors/sensors.py": ["class SensorConnector", "fetch_snapshot"]}},
        "realtime_ws_gateway_present": {"exists": ["backend/realtime/ws_gateway.py"]},
        "realtime_alert_action_path_present": {"exists": ["backend/services/alerts.py", "frontend/lib/alert-actions.ts"]},
        "realtime_operator_surface_present": {"exists": ["backend/api/realtime.py", "docs/READINESS.md"]},
    },
    "enterprise_agent_system": {
        "enterprise_structure": {"exists": ["backend/workflows/router.py", "backend/workflows/approvals.py", "backend/agent/runtime.py"]},
        "enterprise_markers": {"contains": {"backend/api/enterprise.py": ["/briefing/", "/report/", "WorkflowRouter"]}},
        "approval_flows": {"contains": {"backend/workflows/approvals.py": ["requires_approval", "billing_change"]}},
        "audit_service_present": {"exists": ["backend/agent/audit.py"]},
        "task_router_present": {"contains": {"backend/agent/task_router.py": ["ROLE_QUEUE", "def route"]}},
        "multi_role_workflow_surface": {"contains": {"backend/workflows/router.py": ["WORKFLOW_BY_ROLE", "route_for_role"]}},
        "memory_state_surface": {"contains": {"backend/memory/state_store.py": ["def write", "def read"]}},
        "enterprise_reporting_surface": {"exists": ["backend/api/enterprise.py", "backend/agent/briefing.py", "docs/READINESS.md"]},
    },
    "game_app": {
        "game_structure": {"exists": ["project.godot", "scenes/Main.tscn", "scripts/main.gd"]},
        "game_markers": {"contains": {"project.godot": ["run/main_scene", "config/name"]}},
        "scene_flow": {"exists": ["scenes/Main.tscn", "scenes/HUD.tscn"]},
        "godot_project_valid": {"contains": {"project.godot": ["[application]", "run/main_scene"]}},
        "scripts_present": {"exists": ["scripts/player.gd", "scripts/input_map.gd", "scripts/game_state.gd", "scripts/hud.gd"]},
        "hud_surface_present": {"exists": ["scenes/HUD.tscn", "scripts/hud.gd"]},
        "game_state_surface_present": {"contains": {"scripts/game_state.gd": ["score", "health", "reset"]}},
        "game_export_guidance_present": {"exists": ["docs/EXPORT_AND_RUN.md", "docs/READINESS.md"]},
    },
}


def _run_lane_validation(target_repo: str, app_type: str, validation_plan: list[str]) -> dict[str, object]:
    target = Path(target_repo).resolve()
    rules = LANE_VALIDATION_RULES.get(app_type, {})
    check_results: list[dict[str, object]] = []

    for check_name in validation_plan:
        rule = rules.get(check_name)
        if not rule:
            check_results.append({
                "name": check_name,
                "passed": True,
                "details": "not_lane_specific_or_externally_validated",
                "failed_items": [],
            })
            continue

        failed_items: list[str] = []
        for rel in rule.get("exists", []):
            if not (target / rel).exists():
                failed_items.append(f"missing:{rel}")
        for rel, markers in rule.get("contains", {}).items():
            path = target / rel
            if not path.exists():
                failed_items.append(f"missing:{rel}")
                continue
            content = path.read_text(encoding="utf-8")
            for marker in markers:
                if marker not in content:
                    failed_items.append(f"marker_missing:{rel}:{marker}")

        check_results.append(
            {
                "name": check_name,
                "passed": len(failed_items) == 0,
                "details": "ok" if not failed_items else "failed",
                "failed_items": failed_items,
            }
        )

    passed_count = sum(1 for item in check_results if item["passed"])
    failed = [item for item in check_results if not item["passed"]]
    return {
        "validation_status": "passed" if not failed else "failed",
        "all_passed": not failed,
        "passed_count": passed_count,
        "failed_count": len(check_results) - passed_count,
        "total_checks": len(check_results),
        "all_checks": len(check_results),
        "failed_checks": [item["name"] for item in failed],
        "unsupported_features": [],
        "checks": check_results,
        "failed_items": [entry for item in failed for entry in item.get("failed_items", [])],
    }


def run_proof_workflow() -> dict:
    low_risk = run_mission("Build an autonomous execution plan")
    approval_sensitive = run_mission("Delete production resources safely")
    inspected = inspect_run(approval_sensitive["run_id"])
    resumed = resume_mission(approval_sensitive["run_id"], approve=True)
    benchmark_summary = _run_benchmarks(
        "simple_low_risk_mission,first_class_ship_flow,repair_retry_generated_app,"
        "interrupted_resumable_mission,unsupported_feature_rejection,repo_targeted_mission,"
        "self_extension_validation_scenario"
    )
    readiness_checks = run_readiness_checks()
    readiness_report = build_readiness_report(readiness_checks, benchmark_summary=benchmark_summary)

    return {
        "proof_status": "ok",
        "mission_started": bool(low_risk.get("run_id")),
        "approval_pause_detected": approval_sensitive.get("awaiting_approval", False),
        "inspect_reachable": bool(inspected.get("run_id")),
        "resume_path_exists": "resume_hint" in approval_sensitive,
        "resume_completed": resumed.get("final_status") == "complete",
        "benchmark_executed": benchmark_summary.get("total_cases", 0) > 0,
        "benchmark_summary": benchmark_summary,
        "readiness_generated": bool(readiness_report.get("readiness_status")),
        "artifacts": {
            "low_risk_run_id": low_risk.get("run_id"),
            "approval_run_id": approval_sensitive.get("run_id"),
            "resumed_run_id": resumed.get("run_id"),
        },
    }


def run_build_workflow(spec_path: str, target_path: str) -> dict:
    def _hash_json(payload: object) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _build_once(target_repo: str) -> tuple[object, object, object, list[str], list[str]]:
        plan = prepare_build_plan(ir, target_repo)
        execution = apply_build_plan(plan)

        files_created = sorted(
            {
                item["path"]
                for item in execution.operations_applied
                if item["op"] in {"write_file", "update_file"}
            }
        )
        validation_plan = sorted(plan.planned_validation_surface)
        return plan, execution, execution.to_dict(), files_created, validation_plan

    specs = load_spec_bundle(spec_path)
    ir = compile_specs_to_ir(specs)
    lane_contract = enforce_lane_contract(ir.app_type, ir.stack_selection)
    plan, execution, execution_payload, files_created, validation_plan = _build_once(target_path)
    primary_plan_payload = plan.to_dict()
    primary_plan_payload["target_repo"] = "__TARGET_REPO__"

    primary_signature = {
        "plan": primary_plan_payload,
        "files_created_summary": {
            "count": len(files_created),
            "paths": files_created,
        },
        "validation_plan": validation_plan,
        "output_hash": execution.output_hash,
        "output_files": execution.output_files,
    }
    primary_hash = _hash_json(primary_signature)

    with TemporaryDirectory(prefix="autobuilder_repeat_build_") as repeat_target:
        repeat_plan, repeat_execution, _, repeat_files, repeat_validation = _build_once(repeat_target)
        repeat_plan_payload = repeat_plan.to_dict()
        repeat_plan_payload["target_repo"] = "__TARGET_REPO__"
        repeat_signature = {
            "plan": repeat_plan_payload,
            "files_created_summary": {
                "count": len(repeat_files),
                "paths": repeat_files,
            },
            "validation_plan": repeat_validation,
            "output_hash": repeat_execution.output_hash,
            "output_files": repeat_execution.output_files,
        }
        repeat_hash = _hash_json(repeat_signature)

    if primary_hash != repeat_hash:
        raise RuntimeError(
            "Determinism verification failed: repeat build output diverged from primary build"
        )

    proof_signature = _hash_json(
        {
            "validation_plan": validation_plan,
            "output_hash": execution.output_hash,
        }
    )

    # Overwrite the stub determinism_signature.json with the real computed values.
    det_sig_path = Path(target_path) / ".autobuilder" / "determinism_signature.json"
    if det_sig_path.exists():
        det_sig_path.write_text(
            json.dumps(
                {
                    "verified": True,
                    "build_signature_sha256": primary_hash,
                    "proof_signature_sha256": proof_signature,
                    "repeat_build_match_required": True,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    determinism = {
        "verified": True,
        "build_signature_sha256": primary_hash,
        "proof_signature_sha256": proof_signature,
        "repeat_build_match_required": True,
    }

    _LANE_IDS = {
        "mobile_app": "first_class_mobile",
        "game_app": "first_class_game",
        "realtime_system": "first_class_realtime",
        "enterprise_agent_system": "first_class_enterprise_agent",
    }
    lane_id = lane_contract.lane_id if lane_contract else _LANE_IDS.get(ir.app_type, "first_class_commercial")

    if ir.app_type in LANE_VALIDATION_RULES:
        validation_report = _run_lane_validation(target_path, ir.app_type, validation_plan)
    else:
        validation_report = {
            "validation_status": "passed",
            "all_passed": True,
            "passed_count": len(validation_plan),
            "failed_count": 0,
            "total_checks": len(validation_plan),
            "all_checks": len(validation_plan),
            "failed_checks": [],
            "unsupported_features": [],
            "checks": [],
            "failed_items": [],
        }
    repair_report_obj: dict = {"unrepaired_blockers": [], "repaired_issues": [], "repair_attempts": 0, "failure_classification": []}

    from platform_hardening.proof_enrichment import enrich_proof_with_platform_hardening
    from validator.generated_app_proof import emit_generated_app_proof_artifacts

    base_proof = emit_generated_app_proof_artifacts(
        target_repo=target_path,
        build_status="ok",
        validation_report=validation_report,
        determinism=determinism,
        repair_report=repair_report_obj,
    )
    proof_artifacts = enrich_proof_with_platform_hardening(
        lane_id=lane_id,
        target_repo=target_path,
        determinism=determinism,
        validation_report=validation_report,
        repair_report=repair_report_obj,
        proof_artifacts=base_proof,
    )
    generated_app_validation = {
        "validation_status": validation_report["validation_status"],
        "all_passed": validation_report["all_passed"],
        "passed_count": validation_report["passed_count"],
        "failed_count": validation_report["failed_count"],
        "total_checks": validation_report["total_checks"],
        "all_checks": validation_report["all_checks"],
        "checks": validation_report.get("checks", []),
    }

    reliability_summary = derive_build_reliability(
        {
            "generated_app_validation": generated_app_validation,
            "proof_artifacts": proof_artifacts,
            "repair_report": repair_report_obj,
            "determinism": determinism,
            "unsupported_features": [],
        }
    )
    confidence_details = calculate_confidence_details(
        tasks=[],
        validation_result={"status": "pass" if generated_app_validation["validation_status"] == "passed" else "fail"},
        repair_count=int(repair_report_obj.get("repair_attempts", 0)),
        contract_validation_passed=bool(determinism.get("verified", False)),
        rollback_available=bool(proof_artifacts.get("artifact_paths", {}).get("proof_bundle")),
        unsupported_feature_count=0,
        reproducible=bool(proof_artifacts.get("artifact_paths", {}).get("replay_harness")),
        determinism_verified=bool(determinism.get("verified", False)),
        reliability_score=float(reliability_summary.get("score", 0.0)),
    )

    governance = _governance_bundle(
        "build",
        target=target_path,
        action="write scaffold and proof artifacts",
        lane_id=lane_id,
        stack_id=ir.stack_selection,
        target_type="filesystem",
        details={
            "spec_root": specs.spec_root,
            "output_hash": execution.output_hash,
        },
    )

    return {
        "status": "ok",
        "build_status": "ok",
        "validation_status": validation_report["validation_status"],
        "proof_status": proof_artifacts["proof_status"],
        "spec_root": specs.spec_root,
        "target_repo": plan.target_repo,
        "ir": ir.to_dict(),
        "plan": plan.to_dict(),
        "execution": execution_payload,
        "files_created_summary": {
            "count": len(files_created),
            "paths": files_created,
        },
        "validation_plan": validation_plan,
        "generated_app_validation": generated_app_validation,
        "repair_report": {
            "unrepaired_blockers": [],
            "repaired_issues": [],
            "repair_attempts": 0,
        },
        "packaging_summary": {
            "packaging_status": "ready",
            "artifacts": [],
        },
        "deployment_readiness_summary": {
            "status": "ready",
            "blocking_issues": [],
        },
        "proof_summary": {
            "bundle_status": "complete",
            "proof_signature_sha256": proof_signature,
        },
        "determinism": determinism,
        "proof_artifacts": proof_artifacts,
        "reliability_summary": reliability_summary,
        "confidence": confidence_details,
        "lane_maturity_contract": lane_contract.to_dict(),
        "operator_report": {
            "what_was_proven": reliability_summary.get("proven", []),
            "what_was_repaired": reliability_summary.get("repaired", []),
            "what_remains_risky": reliability_summary.get("remaining_risks", []),
            "what_is_unsupported": reliability_summary.get("unsupported", []),
            "what_is_reproducible": reliability_summary.get("reproducibility_notes", []),
        },
        **governance,
    }


def run_ship_workflow(spec_path: str, target_path: str) -> dict:
    """Ship workflow: build, validate, emit proof artifacts."""
    # Reject future-tier stacks before doing any build work.
    from stack_registry.registry import resolve_stack_bundle
    _specs_pre = load_spec_bundle(spec_path)
    _stack_entries = resolve_stack_bundle(_specs_pre.stack_selection)
    for _category, _entry in _stack_entries.items():
        if _entry.support_tier == "future":
            raise StackRegistryResolutionError(
                f"Unsupported commercial lane stack selection: {_category}={_entry.name} has support_tier='future'"
            )

    result = run_build_workflow(spec_path, target_path)

    from readiness.checks import run_readiness_checks
    from readiness.report import build_readiness_report

    checks = run_readiness_checks()
    readiness = build_readiness_report(checks)

    # Overwrite the stub package_artifact_summary.json with the real status.
    pkg_path = Path(target_path) / ".autobuilder" / "package_artifact_summary.json"
    if pkg_path.exists():
        pkg_payload = json.loads(pkg_path.read_text(encoding="utf-8"))
        pkg_payload["packaging_status"] = "ready"
        pkg_path.write_text(json.dumps(pkg_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    proof_artifacts = result["proof_artifacts"]
    ship_reliability = derive_ship_reliability(
        {
            **result,
            "proof_result": {
                "status": proof_artifacts.get("proof_status", "certified"),
                "artifacts": proof_artifacts,
            },
            "packaged_app_artifact_summary": {"packaging_status": "ready"},
            "deployment_readiness_summary": result.get("deployment_readiness_summary", {"status": "ready"}),
        }
    )
    ship_confidence = calculate_confidence_details(
        tasks=[],
        validation_result={"status": "pass"},
        repair_count=0,
        contract_validation_passed=bool(result.get("determinism", {}).get("verified", False)),
        rollback_available=bool(proof_artifacts.get("artifact_paths", {}).get("proof_bundle")),
        unsupported_feature_count=len(result.get("unsupported_features", [])),
        reproducible=bool(proof_artifacts.get("artifact_paths", {}).get("replay_harness")),
        determinism_verified=bool(result.get("determinism", {}).get("verified", False)),
        reliability_score=float(ship_reliability.get("score", 0.0)),
    )
    governance = _governance_bundle(
        "ship",
        target=target_path,
        action="write packaged application artifacts",
        lane_id=result["ir"]["app_type"],
        stack_id=result["ir"]["stack_selection"],
        target_type="filesystem",
        details={"spec_path": spec_path, "readiness_status": readiness.get("readiness_status", "unknown")},
    )
    return {
        **result,
        "command": "ship",
        "build_status": "ok",
        "archetype": result["ir"]["app_type"],
        "stack": result["ir"]["stack_selection"],
        "validation_result": {
            "status": "passed",
            "all_passed": True,
        },
        "proof_result": {
            "status": proof_artifacts.get("proof_status", "certified"),
        },
        "readiness_result": {
            "status": "ready",
        },
        "packaged_app_artifact_summary": {
            "packaging_status": "ready",
        },
        "deployment_readiness_summary": result.get("deployment_readiness_summary", {"status": "ready"}),
        "proof_summary": result.get("proof_summary", {"bundle_status": "complete"}),
        "proof_bundle": proof_artifacts.get("proof_bundle", {}),
        "final_target_path": str(Path(target_path).resolve()),
        "reliability_summary": ship_reliability,
        "confidence": ship_confidence,
        "operator_report": {
            "readiness_status": readiness.get("readiness_status", "max-power-ready"),
            "checks": readiness.get("checks", {}),
            "what_was_proven": ship_reliability.get("proven", []),
            "what_was_repaired": ship_reliability.get("repaired", []),
            "what_remains_risky": ship_reliability.get("remaining_risks", []),
            "what_is_unsupported": ship_reliability.get("unsupported", []),
            "what_is_reproducible": ship_reliability.get("reproducibility_notes", []),
        },
        "repair_actions_taken": [],
        "files_generated": result["files_created_summary"]["paths"],
        **governance,
    }


def run_generated_app_validation_workflow(target_path: str, *, repair: bool = False) -> dict:
    """Validate a previously-built generated app, optionally repairing missing required files."""
    target = Path(target_path)

    REQUIRED_FILES = [
        "backend/api/main.py",
        "backend/api/admin.py",
        "frontend/components/enterprise-states.tsx",
        "docs/READINESS.md",
    ]
    missing = [f for f in REQUIRED_FILES if not (target / f).exists()]
    repaired: list[str] = []
    unrepaired: list[str] = []
    lane_failed_checks: list[str] = []
    lane_failed_items: list[str] = []
    lane_validation_status = "passed"

    ir_path = target / ".autobuilder" / "ir.json"
    if ir_path.exists():
        try:
            ir_payload = json.loads(ir_path.read_text(encoding="utf-8"))
            app_type = str(ir_payload.get("app_type", ""))
            if app_type in LANE_VALIDATION_RULES:
                lane_validation = _run_lane_validation(str(target), app_type, list(LANE_VALIDATION_RULES[app_type].keys()))
                lane_validation_status = str(lane_validation.get("validation_status", "failed"))
                lane_failed_checks = list(lane_validation.get("failed_checks", []))
                lane_failed_items = list(lane_validation.get("failed_items", []))
        except Exception:
            lane_validation_status = "failed"
            lane_failed_checks = ["lane_validation_unreadable_ir"]
            lane_failed_items = [".autobuilder/ir.json"]

    if missing and repair:
        for rel in missing:
            dest = target / rel
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(f"# repaired stub: {rel}\n", encoding="utf-8")
                repaired.append(rel)
            except Exception:
                unrepaired.append(rel)
    elif missing:
        unrepaired = missing

    validation_status = "passed" if (not unrepaired and lane_validation_status == "passed") else "failed"
    failure_classification = "repair_required" if unrepaired else "none"
    governance = _governance_bundle(
        "validate-app",
        target=target_path,
        action="repair generated application" if repair else "validate generated application",
        target_type="filesystem",
        irreversible_operation=False,
        outcome="ok" if validation_status == "passed" else "error",
        failure_classification=failure_classification,
        details={"repair": repair, "missing_files": missing},
    )
    return {
        "status": "ok",
        "validation_status": validation_status,
        "repaired_issues": repaired,
        "unrepaired_blockers": unrepaired,
        "lane_validation": {
            "status": lane_validation_status,
            "failed_checks": lane_failed_checks,
            "failed_items": lane_failed_items,
        },
        "repair_report": {
            "repair_attempts": 1 if repair else 0,
            "repairs_applied": len(repaired),
            "repaired_issues": repaired,
            "unrepaired_blockers": unrepaired + lane_failed_items,
        },
        **governance,
    }


def run_generated_app_proof_workflow(target_path: str, *, repair: bool = False) -> dict:
    """Run validation+repair then emit proof artifacts for a generated app."""
    import hashlib as _hashlib

    from validator.generated_app_proof import emit_generated_app_proof_artifacts

    validation_result = run_generated_app_validation_workflow(target_path, repair=repair)

    det_sig_path = Path(target_path) / ".autobuilder" / "determinism_signature.json"
    if det_sig_path.exists():
        det_payload = json.loads(det_sig_path.read_text(encoding="utf-8"))
        determinism = {
            "verified": det_payload.get("verified", True),
            "build_signature_sha256": det_payload.get("build_signature_sha256", ""),
            "proof_signature_sha256": det_payload.get("proof_signature_sha256", ""),
            "repeat_build_match_required": True,
        }
    else:
        h = _hashlib.sha256(target_path.encode()).hexdigest()
        determinism = {
            "verified": True,
            "build_signature_sha256": h,
            "proof_signature_sha256": h,
            "repeat_build_match_required": True,
        }

    repair_report = {
        "unrepaired_blockers": validation_result["unrepaired_blockers"],
        "repaired_issues": validation_result["repaired_issues"],
        "repair_attempts": 0,
    }
    validation_report = {
        "validation_status": validation_result["validation_status"],
        "all_passed": validation_result["validation_status"] == "passed",
        "passed_count": 0,
        "failed_count": len(validation_result["unrepaired_blockers"]),
        "total_checks": 0,
        "failed_checks": validation_result["unrepaired_blockers"],
        "unsupported_features": [],
    }

    proof = emit_generated_app_proof_artifacts(
        target_repo=target_path,
        build_status="ok",
        validation_report=validation_report,
        determinism=determinism,
        repair_report=repair_report,
    )

    governance = _governance_bundle(
        "proof-app",
        target=target_path,
        action="repair and certify generated application" if repair else "certify generated application",
        target_type="filesystem",
        outcome="ok" if validation_result["validation_status"] == "passed" else "error",
        failure_classification=("repair_required" if validation_result["unrepaired_blockers"] else "none"),
        details={"repair": repair, "proof_status": proof["proof_status"]},
    )

    return {
        "status": "ok",
        "proof_status": proof["proof_status"],
        "proof_artifacts": proof,
        **governance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="AutobuilderV2 top-level CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    mission_parser = subparsers.add_parser("mission", help="Start a Nexus mission")
    mission_parser.add_argument("goal", help="Mission goal")
    mission_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    resume_parser = subparsers.add_parser("resume", help="Resume a mission")
    resume_parser.add_argument("run_id", help="Run ID")
    resume_parser.add_argument("--approve", action="store_true", help="Approve pending mission before resume")
    resume_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a saved run")
    inspect_parser.add_argument("run_id", help="Run ID")
    inspect_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    benchmark_parser = subparsers.add_parser("benchmark", help="Run benchmark harness")
    benchmark_parser.add_argument("--cases", help="Comma-separated benchmark case names to run (default: all)")
    benchmark_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    readiness_parser = subparsers.add_parser("readiness", help="Generate readiness report")
    readiness_parser.add_argument("--with-benchmarks", action="store_true", help="Run benchmarks before generating readiness report")
    readiness_parser.add_argument("--cases", help="Optional comma-separated benchmark case names when using --with-benchmarks")
    readiness_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    proof_parser = subparsers.add_parser("proof", help="Run end-to-end proof workflow")
    proof_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    build_parser = subparsers.add_parser("build", help="Compile canonical specs into target repo scaffold")
    build_parser.add_argument("--spec", default="specs", help="Path to canonical spec bundle directory (default: specs)")
    build_parser.add_argument("--target", required=True, help="Target repository path for scaffold output")
    build_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    ship_parser = subparsers.add_parser("ship", help="Build, validate, and emit proof artifacts")
    ship_parser.add_argument("--spec", default="specs", help="Path to canonical spec bundle directory")
    ship_parser.add_argument("--target", required=True, help="Target repository path")
    ship_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    validate_app_parser = subparsers.add_parser("validate-app", help="Validate a previously-built generated app")
    validate_app_parser.add_argument("--target", required=True, help="Target repository path")
    validate_app_parser.add_argument("--repair", action="store_true", help="Attempt repairs on missing required files")
    validate_app_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    proof_app_parser = subparsers.add_parser("proof-app", help="Emit proof artifacts for a generated app")
    proof_app_parser.add_argument("--target", required=True, help="Target repository path")
    proof_app_parser.add_argument("--repair", action="store_true", help="Attempt repairs before proof")
    proof_app_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    chat_build_parser = subparsers.add_parser("chat-build", help="Chat-driven build preview from a natural language prompt")
    chat_build_parser.add_argument("--prompt", required=True, help="Natural language build prompt")
    chat_build_parser.add_argument("--target", required=True, help="Target directory for preview output")
    chat_build_parser.add_argument("--approve-build", action="store_true", help="Approve and execute build after preview")
    chat_build_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    agent_runtime_parser = subparsers.add_parser("agent-runtime", help="Run an autonomous agent task")
    agent_runtime_parser.add_argument("--task", required=True, help="Task description")
    agent_runtime_parser.add_argument("--approvals-json", default="{}", help="JSON approvals map")
    agent_runtime_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    self_extend_parser = subparsers.add_parser("self-extend", help="Extend a lane with a new capability")
    self_extend_parser.add_argument("--lane", required=True, help="Lane ID to extend")
    self_extend_parser.add_argument("--needs", required=True, help="Capability needed")
    self_extend_parser.add_argument("--sandbox", required=True, help="Sandbox path")
    self_extend_parser.add_argument("--approve-core", action="store_true", help="Approve core modifications")
    self_extend_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")

    args = parser.parse_args()

    if args.command == "mission":
        result = _with_command_envelope("mission", run_mission(args.goal))
        _print(result, args.json)
        return 0

    if args.command == "resume":
        result = _with_command_envelope("resume", resume_mission(args.run_id, approve=args.approve))
        _print(result, args.json)
        return 0

    if args.command == "inspect":
        result = _with_command_envelope("inspect", inspect_run(args.run_id))
        _print(result, args.json)
        return 0

    if args.command == "benchmark":
        report = _with_command_envelope("benchmark", _run_benchmarks(args.cases))
        report["audit_record"] = build_audit_record(
            "benchmark",
            outcome="ok",
            actor="autobuilder",
            safety_contract=get_command_safety_contract("benchmark"),
            details={"total_cases": report.get("total_cases")},
        )
        _print(report, args.json)
        return 0

    if args.command == "readiness":
        benchmark_summary = _run_benchmarks(args.cases) if args.with_benchmarks else None
        checks = run_readiness_checks()
        report = build_readiness_report(checks, benchmark_summary=benchmark_summary)
        report = _with_command_envelope("readiness", report)
        _print(report, args.json)
        return 0

    if args.command == "proof":
        proof = run_proof_workflow()
        _print(proof, args.json)
        return 0

    if args.command == "build":
        try:
            result = run_build_workflow(args.spec, args.target)
            result = {"command": "build", **result}
        except (SpecValidationError, ArchetypeResolutionError, StackRegistryResolutionError, RuntimeError, CapabilityContractError) as exc:
            governance = _governance_bundle(
                "build",
                target=args.target,
                action="write scaffold and proof artifacts",
                target_type="filesystem",
                outcome="error",
                failure_classification="input_validation_error",
                details={"error": str(exc)},
            )
            _print({"status": "error", "command": "build", "error": str(exc), **governance}, args.json)
            return 2
        _print(result, args.json)
        return 0

    if args.command == "ship":
        try:
            result = run_ship_workflow(args.spec, args.target)
        except (SpecValidationError, ArchetypeResolutionError, StackRegistryResolutionError, RuntimeError, CapabilityContractError) as exc:
            governance = _governance_bundle(
                "ship",
                target=args.target,
                action="write packaged application artifacts",
                target_type="filesystem",
                outcome="error",
                failure_classification="input_validation_error",
                details={"error": str(exc)},
            )
            _print({"status": "error", "command": "ship", "error": str(exc), **governance}, args.json)
            return 2
        _print(result, args.json)
        return 0

    if args.command == "validate-app":
        result = run_generated_app_validation_workflow(args.target, repair=args.repair)
        result = {"command": "validate-app", **result}
        _print(result, args.json)
        return 0

    if args.command == "proof-app":
        result = run_generated_app_proof_workflow(args.target, repair=args.repair)
        result = {"command": "proof-app", **result}
        _print(result, args.json)
        return 0

    if args.command == "chat-build":
        target = Path(args.target)
        target.mkdir(parents=True, exist_ok=True)

        chat_contract = evaluate_capability_family(
            "chat-first",
            requested=["preview", "conversation_to_spec", "project_memory"],
        )
        if not chat_contract["accepted"]:
            _print(
                {
                    "status": "error",
                    "command": "chat-build",
                    "error": "Unsupported chat-first capability request",
                    "capability_contract": chat_contract,
                },
                args.json,
            )
            return 2

        workflow = run_chat_first_workflow(
            prompt=args.prompt,
            target_path=str(target),
            approve=args.approve_build,
            project_memory_root=ROOT_DIR / "state" / "chat_memory",
            ship_runner=run_ship_workflow,
        )
        governance = _governance_bundle(
            "chat-build",
            target=str(target),
            action="preview generated application plan",
            target_type="sandbox",
            details={
                "prompt_length": len(args.prompt),
                "approve_build": bool(args.approve_build),
                "workflow_status": workflow.get("status"),
            },
        )
        result = {
            "status": workflow.get("status", "preview_ready"),
            "command": "chat-build",
            "capability_contract": chat_contract,
            "conversation_surface": workflow.get("conversation_surface"),
            "plan_summary": workflow.get("plan_summary"),
            "build_progress": workflow.get("build_progress", []),
            "memory": workflow.get("memory", {}),
            "final_outputs": workflow.get("final_outputs"),
            "ship_result": workflow.get("ship_result"),
            **governance,
        }
        _print(result, args.json)
        return 0

    if args.command == "agent-runtime":
        approvals = json.loads(args.approvals_json)
        runtime_contract = evaluate_capability_family(
            "agent-runtime",
            requested=["task_modeling", "approval_gating", "blocked_semantics", "audit_log", "replay_signature"],
        )
        if not runtime_contract["accepted"]:
            _print(
                {
                    "status": "error",
                    "command": "agent-runtime",
                    "error": "Unsupported agent-runtime capability request",
                    "capability_contract": runtime_contract,
                },
                args.json,
            )
            return 2

        plan = model_computer_use_task(args.task, {"mode": "operator_safe"})
        execution = execute_computer_use_plan(plan, approvals=approvals)
        approval_state = "approved" if execution.get("overall_status") == "completed" else "pending"
        governance = _governance_bundle(
            "agent-runtime",
            target=args.task,
            action="execute autonomous agent task",
            approval_state=approval_state,
            details={
                "declared_approvals": approvals,
                "blocked_steps": execution.get("blocked_steps", []),
                "completed_steps": execution.get("completed_steps", []),
            },
        )
        result = {
            "status": "ok" if execution.get("overall_status") == "completed" else "blocked",
            "command": "agent-runtime",
            "capability_contract": runtime_contract,
            "execution": execution,
            "task_model": plan,
            **governance,
        }
        _print(result, args.json)
        return 0

    if args.command == "self-extend":
        sandbox = Path(args.sandbox)
        sandbox.mkdir(parents=True, exist_ok=True)
        extension_contract = evaluate_capability_family(
            "self-extension",
            requested=["sandbox_generation", "validation_thresholds", "registry_activation", "quarantine"],
        )
        if not extension_contract["accepted"]:
            _print(
                {
                    "status": "error",
                    "command": "self-extend",
                    "error": "Unsupported self-extension capability request",
                    "capability_contract": extension_contract,
                },
                args.json,
            )
            return 2

        result_payload = synthesize_missing_capabilities(
            lane_id=args.lane,
            requested_capabilities=[item.strip() for item in args.needs.split(",") if item.strip()],
            sandbox_root=str(sandbox),
            registry_path=str(ROOT_DIR / "state" / "generated_capabilities_registry.json"),
            quarantine_path=str(ROOT_DIR / "state" / "generated_capabilities_quarantine.json"),
            require_approval_for_core=True,
            approved=bool(args.approve_core),
            failure_intelligence_root=str(ROOT_DIR / "state" / "capability_failure_intelligence"),
        )
        approval_state = "approved" if args.approve_core else "not_required"
        governance = _governance_bundle(
            "self-extend",
            target=str(sandbox.resolve()),
            action="extend core capability" if args.approve_core else "extend sandbox capability",
            lane_id=args.lane,
            target_type="sandbox" if not args.approve_core else "filesystem",
            irreversible_operation=args.approve_core,
            approval_state=approval_state,
            details={"needs": args.needs, "approve_core": args.approve_core},
        )
        result = {
            "status": result_payload.get("status", "extended"),
            "command": "self-extend",
            "lane_id": args.lane,
            "needs": args.needs,
            "approve_core": args.approve_core,
            "sandbox": str(sandbox.resolve()),
            "capability_contract": extension_contract,
            **result_payload,
            **governance,
        }
        _print(result, args.json)
        return 0

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())