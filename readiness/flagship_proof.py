"""
Flagship-proof readiness layer.
Provides mission bundles, readiness bundles, operator runbooks,
final truth-audit checks, and launch/readiness evidence surfaces.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Readiness check library
# ---------------------------------------------------------------------------

_FLAGSHIP_READINESS_CHECKS: list[tuple[str, str]] = [
    ("mission_runner_present", "cli/mission.py"),
    ("resume_path_present", "cli/resume.py"),
    ("inspect_path_present", "cli/inspect.py"),
    ("benchmark_harness_present", "benchmarks/runner.py"),
    ("mutation_safety_present", "mutation/safety.py"),
    ("mutation_provenance_present", "mutation/provenance.py"),
    ("restore_support_present", "state/restore.py"),
    ("memory_policy_present", "memory/policy.py"),
    ("quality_reporting_present", "quality/report.py"),
    ("adapter_registry_present", "adapters/registry.py"),
    ("multimodal_world_state_present", "universal_capability/multimodal_world_state.py"),
    ("vertical_packs_present", "platform_hardening/packs.py"),
    ("security_governance_present", "platform_hardening/security_governance.py"),
    ("commerce_present", "platform_hardening/commerce.py"),
    ("ir_compiler_present", "ir/compiler.py"),
    ("template_packs_present", "generator/template_packs.py"),
    ("stack_registry_present", "stack_registry/registry.py"),
    ("plugin_registry_present", "platform_plugins/registry.py"),
    ("planner_present", "planner/planner.py"),
    ("executor_present", "execution/executor.py"),
    ("flagship_proof_present", "readiness/flagship_proof.py"),
]


def run_flagship_readiness_checks(repo_root: Optional[str] = None) -> dict:
    """Run all flagship readiness checks against the repo."""
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[1]
    checks = []
    for name, relative_path in _FLAGSHIP_READINESS_CHECKS:
        path = root / relative_path
        passed = path.exists()
        checks.append({
            "name": name,
            "passed": passed,
            "path": relative_path,
            "details": "present" if passed else "missing",
        })
    passed_count = sum(1 for c in checks if c["passed"])
    return {
        "checks": checks,
        "passed_count": passed_count,
        "failed_count": len(checks) - passed_count,
        "total_checks": len(checks),
        "all_passed": passed_count == len(checks),
        "readiness_score": round(passed_count / len(checks), 3),
    }


# ---------------------------------------------------------------------------
# Readiness bundle
# ---------------------------------------------------------------------------

@dataclass
class ReadinessBundle:
    bundle_id: str
    mission_run_id: str
    goal: str
    readiness_checks: dict
    capability_requirements: list
    mission_plan: dict
    quality_report: dict
    artifact_lineage: dict
    operator_runbook: dict
    truth_audit: dict
    launch_evidence: dict
    bundle_signature: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _sig(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:24]


def build_operator_runbook(goal: str, mission_result: dict) -> dict:
    """Build a clear operator-facing runbook from a mission result."""
    status = mission_result.get("final_status", "unknown")
    caps = mission_result.get("capability_requirements", [])
    return {
        "runbook_version": "v1",
        "goal": goal,
        "mission_status": status,
        "capability_families": [c.get("family", "unknown") for c in caps],
        "operator_steps": [
            "1. Review mission_plan for capability routing decisions",
            "2. Check quality_report.confidence — if < 0.8, review repair_count",
            "3. If awaiting_approval, approve via: python cli/mission.py --resume <run_id> --approve",
            "4. If checkpoint_available, restore is available at restore_payload.checkpoint_id",
            "5. Review artifact_lineage for all generated artifact ids",
            "6. Run benchmark suite to verify regression safety: python cli/autobuilder.py benchmark",
        ],
        "approval_workflow": {
            "required": mission_result.get("approval_required", False),
            "resume_hint": mission_result.get("resume_hint", "not_required"),
        },
        "restore_workflow": {
            "available": mission_result.get("restore_payload") is not None,
            "restore_hint": mission_result.get("restore_hint", "no_restore_needed"),
        },
        "known_limitations": [
            "executor is bounded — real external code execution not performed",
            "multimodal modalities are structural contracts only",
            "commerce/auth require operator provider credential wiring",
        ],
        "next_actions": (mission_result.get("operator_summary") or {}).get("next_action", "review"),
    }


def build_truth_audit(repo_root: Optional[str] = None) -> dict:
    """Run a final truth-audit check against system claims."""
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[1]
    checks = []

    # Check maturity honesty declarations
    security_gov = root / "platform_hardening" / "security_governance.py"
    if security_gov.exists():
        content = security_gov.read_text(encoding="utf-8")
        checks.append({
            "check": "security_maturity_honest",
            "passed": '"bounded_prototype"' in content,
            "note": "security_governance.py declares bounded_prototype maturity",
        })

    commerce_py = root / "platform_hardening" / "commerce.py"
    if commerce_py.exists():
        content = commerce_py.read_text(encoding="utf-8")
        checks.append({
            "check": "commerce_maturity_honest",
            "passed": '"bounded_prototype"' in content,
            "note": "commerce.py declares bounded_prototype maturity",
        })

    multimodal = root / "universal_capability" / "multimodal_world_state.py"
    if multimodal.exists():
        content = multimodal.read_text(encoding="utf-8")
        checks.append({
            "check": "multimodal_maturity_honest",
            "passed": '"structural_only"' in content,
            "note": "multimodal_world_state.py declares structural_only maturity",
        })

    adapters_reg = root / "adapters" / "registry.py"
    if adapters_reg.exists():
        content = adapters_reg.read_text(encoding="utf-8")
        checks.append({
            "check": "adapters_validated",
            "passed": "validated=True" in content,
            "note": "adapter registry has validated adapters",
        })

    # Check limitation declarations
    mutation_safety = root / "mutation" / "safety.py"
    if mutation_safety.exists():
        checks.append({
            "check": "mutation_safety_present",
            "passed": True,
            "note": "mutation safety policy present",
        })

    passed = sum(1 for c in checks if c["passed"])
    return {
        "truth_audit_version": "v1",
        "checks": checks,
        "passed_count": passed,
        "total_checks": len(checks),
        "all_passed": passed == len(checks),
        "truth_score": round(passed / len(checks), 3) if checks else 0.0,
    }


def build_launch_evidence(mission_result: dict, readiness_checks: dict) -> dict:
    """Build launch/readiness evidence surface."""
    confidence = float(mission_result.get("confidence", 0.0))
    all_ready = readiness_checks.get("all_passed", False)
    readiness_score = readiness_checks.get("readiness_score", 0.0)

    launch_ready = all_ready and confidence >= 0.7
    return {
        "launch_evidence_version": "v1",
        "launch_ready": launch_ready,
        "readiness_score": readiness_score,
        "mission_confidence": confidence,
        "evidence_items": [
            {
                "item": "all_flagship_checks_pass",
                "value": all_ready,
                "required": True,
            },
            {
                "item": "mission_confidence_threshold",
                "value": confidence >= 0.7,
                "threshold": 0.7,
                "actual": confidence,
                "required": True,
            },
            {
                "item": "no_unresolved_dangerous_mutations",
                "value": mission_result.get("mutation_risk") != "dangerous",
                "required": True,
            },
            {
                "item": "artifact_lineage_present",
                "value": bool(mission_result.get("artifact_lineage_summary")),
                "required": False,
            },
            {
                "item": "quality_report_present",
                "value": bool(mission_result.get("quality_report")),
                "required": False,
            },
        ],
        "blocking_issues": [
            item["item"]
            for item in [
                {"item": "all_flagship_checks_pass", "value": all_ready},
                {"item": "mission_confidence_threshold", "value": confidence >= 0.7},
                {"item": "no_unresolved_dangerous_mutations", "value": mission_result.get("mutation_risk") != "dangerous"},
            ]
            if not item["value"]
        ],
    }


def build_flagship_readiness_bundle(
    mission_result: dict,
    repo_root: Optional[str] = None,
) -> ReadinessBundle:
    """Assemble a full flagship readiness bundle from a mission result."""
    run_id = mission_result.get("run_id", "unknown")
    goal = mission_result.get("goal", "")

    readiness_checks = run_flagship_readiness_checks(repo_root)
    operator_runbook = build_operator_runbook(goal, mission_result)
    truth_audit = build_truth_audit(repo_root)
    launch_evidence = build_launch_evidence(mission_result, readiness_checks)

    bundle_data = {
        "run_id": run_id,
        "goal": goal,
        "readiness_score": readiness_checks["readiness_score"],
        "truth_score": truth_audit["truth_score"],
        "launch_ready": launch_evidence["launch_ready"],
    }

    return ReadinessBundle(
        bundle_id=f"flagship-{run_id}",
        mission_run_id=run_id,
        goal=goal,
        readiness_checks=readiness_checks,
        capability_requirements=mission_result.get("capability_requirements", []),
        mission_plan=mission_result.get("mission_plan", {}),
        quality_report=mission_result.get("quality_report", {}),
        artifact_lineage=mission_result.get("artifact_lineage_summary", {}),
        operator_runbook=operator_runbook,
        truth_audit=truth_audit,
        launch_evidence=launch_evidence,
        bundle_signature=_sig(bundle_data),
    )


def emit_flagship_bundle_to_disk(
    bundle: ReadinessBundle,
    output_dir: Optional[str] = None,
) -> dict:
    """Write flagship readiness bundle to disk."""
    root = Path(output_dir) if output_dir else Path(__file__).resolve().parents[1] / "runs"
    root.mkdir(parents=True, exist_ok=True)
    bundle_path = root / f"{bundle.bundle_id}.flagship_bundle.json"
    bundle_path.write_text(
        json.dumps(bundle.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "bundle_path": str(bundle_path),
        "bundle_id": bundle.bundle_id,
        "launch_ready": bundle.launch_evidence["launch_ready"],
        "readiness_score": bundle.readiness_checks["readiness_score"],
        "truth_score": bundle.truth_audit["truth_score"],
    }
