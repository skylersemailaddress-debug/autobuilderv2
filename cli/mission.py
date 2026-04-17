import argparse
import io
import json
import sys
import uuid
from contextlib import redirect_stdout
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ensure top-level package imports work when executing cli/mission.py directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from cli.resume import resume_saved_run
from cli.run import perform_run
from control_plane.approvals import ApprovalRequest, transition_approval
from execution.lineage import build_artifact_lineage, summarize_artifact_lineage
from mutation.change_set import ChangeSet
from mutation.safety import DANGEROUS, MutationSafetyPolicy
from quality.report import build_mission_quality_report
from runs.summary import build_run_summary
from state.audit import append_audit_event, build_audit_record
from state.json_store import JsonRunStore
from state.restore import latest_restore_payload


# ---------------------------------------------------------------------------
# Capability requirement derivation
# ---------------------------------------------------------------------------

_CAPABILITY_KEYWORD_MAP: List[Tuple[List[str], str, str]] = [
    (["auth", "login", "rbac", "permission", "role", "session", "oauth", "jwt"], "security", "auth_authz"),
    (["payment", "billing", "invoice", "subscription", "entitlement", "commerce", "stripe"], "commerce", "billing_commerce"),
    (["realtime", "stream", "event", "sensor", "telemetry", "websocket", "pubsub"], "realtime", "realtime_ingestion"),
    (["agent", "assistant", "workflow", "orchestrat", "automat"], "agent-runtime", "agent_workflow"),
    (["mobile", "flutter", "ios", "android", "offline", "sync"], "mobile", "mobile_client"),
    (["game", "scene", "player", "physics", "sprite", "godot"], "game", "game_engine"),
    (["validate", "proof", "contract", "check", "test", "verify"], "validation", "validation_proof"),
    (["adapter", "connect", "bridge", "integration", "webhook", "api"], "adapter", "external_connector"),
    (["image", "photo", "vision", "document", "pdf", "ocr"], "multimodal", "image_document_processing"),
    (["audio", "speech", "voice", "sound", "transcri"], "multimodal", "audio_processing"),
    (["monitor", "alert", "dashboard", "observ", "metric", "log"], "observability", "monitoring_alerting"),
    (["admin", "reporting", "backoffice", "operator", "audit"], "enterprise", "admin_reporting"),
    (["regulated", "compliance", "hipaa", "gdpr", "policy", "governance"], "regulated", "regulated_compliance"),
    (["migrate", "refactor", "update", "patch", "repair", "evolve"], "repo-mutation", "repo_evolution"),
]

_ACQUISITION_ROUTE_MAP: Dict[str, str] = {
    "security": "use_existing",
    "commerce": "compose_existing",
    "realtime": "use_existing",
    "agent-runtime": "compose_existing",
    "mobile": "use_existing",
    "game": "use_existing",
    "validation": "use_existing",
    "adapter": "generate_adapter",
    "multimodal": "generate_pack",
    "observability": "generate_pack",
    "enterprise": "compose_existing",
    "regulated": "generate_contract",
    "repo-mutation": "use_existing",
    "domain": "generate_pack",
}


def _derive_capability_requirements(goal: str) -> List[Dict]:
    """Analyze goal text to derive structured capability requirements."""
    lowered = goal.lower()
    requirements: List[Dict] = []
    seen_families: set = set()
    for keywords, family, cap_id in _CAPABILITY_KEYWORD_MAP:
        if any(kw in lowered for kw in keywords):
            if family not in seen_families:
                seen_families.add(family)
                requirements.append({
                    "capability_id": cap_id,
                    "family": family,
                    "acquisition_route": _ACQUISITION_ROUTE_MAP.get(family, "generate_pack"),
                    "required": True,
                })
    if not requirements:
        requirements.append({
            "capability_id": "general_build",
            "family": "domain",
            "acquisition_route": "generate_pack",
            "required": True,
        })
    return requirements


def _build_machine_readable_mission_plan(
    run_id: str,
    goal: str,
    change_set: ChangeSet,
    capability_requirements: List[Dict],
    state: str = "planned",
) -> Dict:
    """Emit a machine-readable mission plan/state record."""
    return {
        "schema_version": "v2",
        "mission_plan_id": f"plan-{run_id}",
        "run_id": run_id,
        "goal": goal,
        "state": state,  # planned | executing | paused_approval | complete | failed | interrupted
        "capability_requirements": capability_requirements,
        "routing_summary": {
            family_req["family"]: family_req["acquisition_route"]
            for family_req in capability_requirements
        },
        "change_envelope": {
            "action": change_set.action,
            "action_class": change_set.action_class,
            "target_type": change_set.target_type,
            "risk_level": change_set.risk_level,
            "requires_checkpoint": change_set.requires_checkpoint,
            "approval_required": change_set.risk_level == DANGEROUS,
            "irreversible_operation": change_set.irreversible_operation,
            "rollback_strategy": change_set.rollback_strategy,
        },
        "pause_resume_semantics": {
            "supports_pause": True,
            "supports_resume": True,
            "supports_approval_gate": True,
            "supports_interruption_recovery": True,
            "checkpoint_available": change_set.requires_checkpoint,
        },
        "operator_summary_url": f"runs/{run_id}.mission.json",
    }


def _mission_result_path(run_id: str) -> Path:
    return ROOT_DIR / "runs" / f"{run_id}.mission.json"


def _build_resume_hint(run_id: str) -> str:
    return (
        f"Approval required. Approve run in runs/{run_id}.json, then run "
        f"python cli/mission.py --resume {run_id} --approve"
    )


def _infer_action_target(goal: str) -> Tuple[str, str]:
    lowered = goal.lower()
    if "delete" in lowered or "destroy" in lowered:
        return "delete", goal
    if "rename" in lowered:
        return "rename", goal
    if "migrate" in lowered:
        return "migrate", goal
    if "update" in lowered or "modify" in lowered or "edit" in lowered or "write" in lowered:
        return "update", goal
    if "create" in lowered or "add" in lowered or "new" in lowered:
        return "create", goal
    return "create", goal


def _plan_change_set(goal: str) -> ChangeSet:
    action, target = _infer_action_target(goal)
    policy = MutationSafetyPolicy()
    decision = policy.evaluate(action, target)
    return ChangeSet(
        change_id=f"change-{uuid.uuid4().hex[:12]}",
        action=action,
        target=target,
        risk_level=decision.risk_level,
        requires_checkpoint=decision.checkpoint_required,
        approved=False,
        applied=False,
        action_class=decision.action_class,
        target_type=decision.target_type,
        destructive_potential=decision.destructive_potential,
        environment_sensitivity=decision.environment_sensitivity,
        irreversible_operation=decision.irreversible_operation,
        rollback_strategy=decision.restore_strategy,
    )


def _build_operator_summary(record: Dict) -> Dict:
    """Produce a clear operator-facing result summary."""
    status = record.get("status", "unknown")
    confidence = record.get("confidence", 0.0)
    repair_count = record.get("repair_count", 0)
    caps = record.get("capability_requirements", [])
    cap_families = [c.get("family", "unknown") for c in caps]
    mission_state = (record.get("mission_plan") or {}).get("state", "unknown")
    return {
        "status": status,
        "mission_state": mission_state,
        "confidence": confidence,
        "repair_count": repair_count,
        "capability_families_used": cap_families,
        "approval_required": record.get("awaiting_approval", False),
        "checkpoint_available": record.get("checkpoint_required", False),
        "restore_available": record.get("restore_available", False),
        "interruption_recovery_supported": True,
        "result_bundle": f"runs/{record.get('run_id', 'unknown')}.mission.json",
        "next_action": (
            "approve and resume" if record.get("awaiting_approval")
            else ("review quality report" if confidence < 0.8 else "mission complete")
        ),
    }


def build_mission_result(record: Dict, saved_path: str) -> Dict:
    summary = record.get("summary", {})
    approval_required = summary.get(
        "approval_required",
        record.get("policy", {}).get("approval_required", False),
    )
    awaiting_approval = record.get("awaiting_approval", False)
    change_sets = record.get("change_sets", [])
    mutation_risk = record.get("mutation_risk", "safe")
    checkpoint_required = any(item.get("requires_checkpoint", False) for item in change_sets)
    restore_payload = record.get("restore_payload")
    lineage_summary = summarize_artifact_lineage(
        record.get("run_id"),
        record.get("artifacts", []),
        record.get("checkpoints", []),
    )
    quality_report = record.get("quality_report")
    audit_record = record.get("audit_record")
    audit_trail = record.get("audit_trail", [])

    if mutation_risk == DANGEROUS:
        approval_required = True

    result = {
        "run_id": record.get("run_id"),
        "goal": record.get("goal"),
        "final_status": record.get("status", summary.get("final_status")),
        "approval_required": approval_required,
        "awaiting_approval": awaiting_approval,
        "confidence": record.get("confidence", summary.get("confidence", 0.0)),
        "repair_count": record.get("repair_count", 0),
        "summary": summary,
        "change_sets": change_sets,
        "mutation_risk": mutation_risk,
        "checkpoint_required": checkpoint_required,
        "restore_payload": restore_payload,
        "artifact_lineage_summary": lineage_summary,
        "quality_report": quality_report,
        "audit_record": audit_record,
        "audit_event_count": len(audit_trail),
        "saved_path": saved_path,
        "capability_requirements": record.get("capability_requirements", []),
        "mission_plan": record.get("mission_plan", {}),
        "operator_summary": _build_operator_summary(record),
    }
    if awaiting_approval:
        result["resume_hint"] = _build_resume_hint(record["run_id"])
    if checkpoint_required and restore_payload:
        result["restore_hint"] = (
            f"Restore payload available for checkpoint {restore_payload.get('checkpoint_id')} "
            f"in runs/{record['run_id']}.json"
        )
    return result


def _save_mission_result(result: Dict) -> str:
    path = _mission_result_path(result["run_id"])
    with path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    return str(path)


def run_mission(goal: str) -> Dict:
    run_id = f"mission_{uuid.uuid4().hex}"
    planned_change = _plan_change_set(goal)
    capability_requirements = _derive_capability_requirements(goal)
    mission_plan = _build_machine_readable_mission_plan(
        run_id, goal, planned_change, capability_requirements, state="executing"
    )
    with io.StringIO() as capture, redirect_stdout(capture):
        record, saved_path = perform_run(run_id=run_id, goal=goal, nexus_mode_enabled=True)

    change_set = asdict(planned_change)
    change_set["approved"] = record.get("awaiting_approval", False) is False
    change_set["applied"] = record.get("status") == "complete"
    record["change_sets"] = [change_set]
    record["mutation_risk"] = change_set["risk_level"]
    record["checkpoint_required"] = change_set["requires_checkpoint"]
    record["capability_requirements"] = capability_requirements
    record["mission_plan"] = {
        **mission_plan,
        "state": "complete" if record.get("status") == "complete" else (
            "paused_approval" if record.get("awaiting_approval") else "failed"
        ),
    }
    record["artifact_lineage"] = build_artifact_lineage(
        run_id,
        record.get("artifacts", []),
        record.get("checkpoints", []),
    )
    if change_set["requires_checkpoint"]:
        record["restore_payload"] = latest_restore_payload(record)
    else:
        record["restore_payload"] = None
    restore_payload = record.get("restore_payload") or {}
    record["restore_available"] = bool(restore_payload.get("restore_possible"))
    record["audit_trail"] = append_audit_event(
        record.get("audit_trail", []),
        "mission_result_built",
        actor="mission",
        details={"mutation_risk": record["mutation_risk"], "checkpoint_required": record["checkpoint_required"]},
    )
    record["audit_record"] = build_audit_record(
        "mission",
        outcome=record.get("status", "unknown"),
        run_id=run_id,
        risk_level=record["mutation_risk"],
        approval_state=(record.get("approval_request") or {}).get("status", "not_required"),
        checkpoint_ids=[item["checkpoint_id"] for item in record.get("checkpoints", [])],
        rollback_ready=record["restore_available"],
        restore_checkpoint_id=restore_payload.get("checkpoint_id"),
        actor="mission",
        details={"goal": goal, "change_set_count": len(record["change_sets"])},
    )
    record["summary"] = build_run_summary(record)
    record["quality_report"] = build_mission_quality_report(
        record,
        benchmark_summary=record.get("benchmark_summary"),
    )

    store = JsonRunStore(base_dir=ROOT_DIR / "runs")
    store.save(run_id, record)

    result = build_mission_result(record, saved_path)
    result["mission_result_path"] = _save_mission_result(result)
    return result


def resume_mission(run_id: str, approve: bool = False) -> Dict:
    store = JsonRunStore(base_dir=ROOT_DIR / "runs")
    record = store.load(run_id)
    if record is None:
        raise FileNotFoundError(f"Run record {run_id} not found")

    if approve and record.get("awaiting_approval"):
        approval_request = record.get("approval_request")
        if approval_request:
            updated_request = transition_approval(
                ApprovalRequest(**approval_request),
                "approved",
                approver_identity="mission-operator",
                decision_reason="Mission resume approved by operator",
                actor="mission-operator",
                metadata={"resume_run_id": run_id},
            )
            record["approval_request"] = asdict(updated_request)
            record["audit_trail"] = append_audit_event(
                record.get("audit_trail", []),
                "approval_granted",
                actor="mission-operator",
                details={"approval_id": updated_request.approval_id},
            )
            store.save(run_id, record)

    with io.StringIO() as capture, redirect_stdout(capture):
        resumed_record, saved_path = resume_saved_run(run_id)
    if resumed_record is None:
        raise FileNotFoundError(f"Run record {run_id} not found")

    normalized_saved_path = saved_path or str(ROOT_DIR / "runs" / f"{run_id}.json")
    existing_change_sets = record.get("change_sets", [])
    resumed_record["change_sets"] = existing_change_sets
    resumed_record["mutation_risk"] = record.get("mutation_risk", "safe")
    resumed_record["checkpoint_required"] = any(
        item.get("requires_checkpoint", False) for item in existing_change_sets
    )
    resumed_record["artifact_lineage"] = build_artifact_lineage(
        run_id,
        resumed_record.get("artifacts", []),
        resumed_record.get("checkpoints", []),
    )
    if resumed_record.get("checkpoint_required"):
        resumed_record["restore_payload"] = latest_restore_payload(resumed_record)
    else:
        resumed_record["restore_payload"] = None
    resumed_restore_payload = resumed_record.get("restore_payload") or {}
    resumed_record["restore_available"] = bool(resumed_restore_payload.get("restore_possible"))
    resumed_record["audit_trail"] = append_audit_event(
        resumed_record.get("audit_trail", []),
        "mission_resumed",
        actor="mission",
        details={"approved": approve, "final_status": resumed_record.get("status")},
    )
    resumed_record["audit_record"] = build_audit_record(
        "mission",
        outcome=resumed_record.get("status", "unknown"),
        run_id=run_id,
        risk_level=resumed_record.get("mutation_risk", "safe"),
        approval_state=(resumed_record.get("approval_request") or {}).get("status", "not_required"),
        checkpoint_ids=[item["checkpoint_id"] for item in resumed_record.get("checkpoints", [])],
        rollback_ready=resumed_record["restore_available"],
        restore_checkpoint_id=resumed_restore_payload.get("checkpoint_id"),
        actor="mission",
        details={"change_set_count": len(existing_change_sets), "resumed": True},
    )
    resumed_record["summary"] = build_run_summary(resumed_record)
    resumed_record["quality_report"] = build_mission_quality_report(
        resumed_record,
        benchmark_summary=resumed_record.get("benchmark_summary"),
    )
    store.save(run_id, resumed_record)

    result = build_mission_result(resumed_record, normalized_saved_path)
    result["mission_result_path"] = _save_mission_result(result)
    return result


def _print_result(result: Dict, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(result, indent=2))
        return

    print(f"run_id={result['run_id']}")
    print(f"goal={result['goal']}")
    print(f"final_status={result['final_status']}")
    print(f"approval_required={result['approval_required']}")
    print(f"awaiting_approval={result['awaiting_approval']}")
    print(f"confidence={result['confidence']}")
    print(f"repair_count={result['repair_count']}")
    print(f"saved_path={result['saved_path']}")
    print(f"mission_result_path={result['mission_result_path']}")
    if result.get("resume_hint"):
        print(f"resume_hint={result['resume_hint']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or resume one-button Nexus missions")
    parser.add_argument("goal", nargs="?", help="Goal to execute as a Nexus mission")
    parser.add_argument("--resume", dest="resume_run_id", help="Run ID of a mission to resume")
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Mark pending approval as approved before resume",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full mission result as JSON",
    )
    args = parser.parse_args()

    if args.resume_run_id:
        result = resume_mission(args.resume_run_id, approve=args.approve)
    elif args.goal:
        result = run_mission(args.goal)
    else:
        parser.error("Provide a goal or use --resume <run_id>.")

    _print_result(result, as_json=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())