from __future__ import annotations

from typing import Dict, Iterable


RELIABILITY_WEIGHTS = {
    "determinism": 0.2,
    "repair_success": 0.15,
    "proof_completeness": 0.15,
    "validation_completeness": 0.2,
    "rollback_availability": 0.1,
    "unsupported_feature_handling": 0.1,
    "reproducibility": 0.1,
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 4)))


def _average(values: Iterable[float]) -> float:
    collected = [float(value) for value in values]
    if not collected:
        return 0.0
    return sum(collected) / len(collected)


def _grade(score: float) -> str:
    if score >= 0.95:
        return "trusted"
    if score >= 0.85:
        return "strong"
    if score >= 0.7:
        return "acceptable"
    if score >= 0.5:
        return "watch"
    return "weak"


def build_reliability_summary(
    flow: str,
    component_scores: Dict[str, float],
    *,
    proven: list[str] | None = None,
    repaired: list[str] | None = None,
    remaining_risks: list[str] | None = None,
    unsupported: list[str] | None = None,
    reproducibility_notes: list[str] | None = None,
    evidence: Dict[str, object] | None = None,
) -> Dict[str, object]:
    components = {
        key: _clamp(component_scores.get(key, 0.0))
        for key in RELIABILITY_WEIGHTS
    }
    score = _clamp(
        sum(components[key] * RELIABILITY_WEIGHTS[key] for key in RELIABILITY_WEIGHTS)
    )
    return {
        "flow": flow,
        "score": score,
        "grade": _grade(score),
        "components": components,
        "proven": list(proven or []),
        "repaired": list(repaired or []),
        "remaining_risks": list(remaining_risks or []),
        "unsupported": sorted(str(item) for item in (unsupported or [])),
        "reproducibility_notes": list(reproducibility_notes or []),
        "evidence": dict(evidence or {}),
    }


def derive_run_reliability(record: Dict[str, object]) -> Dict[str, object]:
    tasks = list(record.get("tasks", []))
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.get("status") == "complete")
    validation = record.get("validation_result") or {}
    checkpoint_required = bool(record.get("checkpoint_required", False))
    restore_available = bool((record.get("restore_payload") or {}).get("restore_possible", False))
    repair_count = int(record.get("repair_count", 0))
    failures = list(record.get("failures", []))
    unsupported = list(record.get("unsupported_features", []))
    contract_validation_passed = bool(record.get("contract_validation_passed", False))
    summary_present = bool(record.get("summary"))
    audit_present = bool(record.get("audit_record"))
    quality_present = bool(record.get("quality_report"))

    validation_completeness = 1.0 if total_tasks == 0 else completed_tasks / total_tasks
    if isinstance(validation, dict) and validation.get("status") == "pass":
        validation_completeness = 1.0

    proof_completeness = _average(
        [
            1.0 if summary_present else 0.0,
            1.0 if audit_present else 0.0,
            1.0 if quality_present else 0.0,
            1.0 if record.get("events") else 0.0,
            1.0 if record.get("checkpoints") else 0.0,
        ]
    )
    repair_success = 1.0 if not failures and record.get("status") == "complete" else 0.6
    if repair_count > 0 and record.get("status") == "complete":
        repair_success = max(0.75, 1.0 - (repair_count * 0.08))
    if record.get("status") == "failed":
        repair_success = 0.0
    rollback_availability = 1.0 if (restore_available or not checkpoint_required) else 0.0
    unsupported_feature_handling = 1.0 if not unsupported else 0.0
    reproducibility = 1.0 if contract_validation_passed else 0.5
    determinism = 1.0 if contract_validation_passed else 0.4

    proven = []
    if contract_validation_passed:
        proven.append("run contract validation passed")
    if audit_present:
        proven.append("audit trail recorded")
    if restore_available:
        proven.append("rollback restore payload available")

    repaired = []
    if repair_count > 0:
        repaired.append(f"repair loop completed {repair_count} time(s)")

    remaining_risks = []
    if record.get("awaiting_approval"):
        remaining_risks.append("operator approval still required")
    if failures:
        remaining_risks.extend(sorted({str(item.get("failure_type", "unknown")) for item in failures}))
    if checkpoint_required and not restore_available:
        remaining_risks.append("checkpoint required without restore payload")

    reproducibility_notes = []
    if contract_validation_passed:
        reproducibility_notes.append("contract-validated run summary")
    if record.get("audit_trail"):
        reproducibility_notes.append("audit events preserved")

    return build_reliability_summary(
        "run",
        {
            "determinism": determinism,
            "repair_success": repair_success,
            "proof_completeness": proof_completeness,
            "validation_completeness": validation_completeness,
            "rollback_availability": rollback_availability,
            "unsupported_feature_handling": unsupported_feature_handling,
            "reproducibility": reproducibility,
        },
        proven=proven,
        repaired=repaired,
        remaining_risks=remaining_risks,
        unsupported=unsupported,
        reproducibility_notes=reproducibility_notes,
        evidence={
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "repair_count": repair_count,
            "checkpoint_required": checkpoint_required,
            "restore_available": restore_available,
        },
    )


def derive_build_reliability(result: Dict[str, object]) -> Dict[str, object]:
    validation = dict(result.get("generated_app_validation", {}))
    proof_artifacts = dict(result.get("proof_artifacts", {}))
    determinism_payload = dict(result.get("determinism", {}))
    repair_report = dict(result.get("repair_report", {}))
    unsupported = list(result.get("unsupported_features", []))
    artifact_paths = dict(proof_artifacts.get("artifact_paths", {}))

    total_checks = max(int(validation.get("total_checks", 0)), 1)
    passed_count = int(validation.get("passed_count", 0))
    validation_completeness = passed_count / total_checks if total_checks else 0.0
    proof_completeness = _average(
        [
            1.0 if artifact_paths.get("proof_report") else 0.0,
            1.0 if artifact_paths.get("readiness_report") else 0.0,
            1.0 if artifact_paths.get("validation_summary") else 0.0,
            1.0 if artifact_paths.get("determinism_signature") else 0.0,
            1.0 if artifact_paths.get("replay_harness") else 0.0,
        ]
    )
    determinism = 1.0 if determinism_payload.get("verified", False) else 0.0
    repair_success = 1.0 if not repair_report.get("unrepaired_blockers") else 0.0
    if repair_report.get("repaired_issues") and repair_success == 1.0:
        repair_success = 0.9
    rollback_availability = 1.0 if artifact_paths.get("proof_bundle") else 0.5
    unsupported_feature_handling = 1.0 if not unsupported else 0.0
    reproducibility = 1.0 if artifact_paths.get("replay_harness") and determinism_payload.get("verified", False) else 0.5

    proven = []
    if validation.get("validation_status") == "passed":
        proven.append("generated app validation passed")
    if str(proof_artifacts.get("proof_status", "")).startswith("certified"):
        proven.append("proof artifacts certified")
    if determinism_payload.get("verified", False):
        proven.append("deterministic rebuild signature verified")

    repaired = [str(item) for item in repair_report.get("repaired_issues", [])]
    remaining_risks = [str(item) for item in repair_report.get("unrepaired_blockers", [])]
    reproducibility_notes = []
    if artifact_paths.get("replay_harness"):
        reproducibility_notes.append("replay harness emitted")
    if determinism_payload.get("build_signature_sha256"):
        reproducibility_notes.append("build signature recorded")

    return build_reliability_summary(
        "build",
        {
            "determinism": determinism,
            "repair_success": repair_success,
            "proof_completeness": proof_completeness,
            "validation_completeness": validation_completeness,
            "rollback_availability": rollback_availability,
            "unsupported_feature_handling": unsupported_feature_handling,
            "reproducibility": reproducibility,
        },
        proven=proven,
        repaired=repaired,
        remaining_risks=remaining_risks,
        unsupported=unsupported,
        reproducibility_notes=reproducibility_notes,
        evidence={
            "total_checks": total_checks,
            "passed_count": passed_count,
            "proof_status": proof_artifacts.get("proof_status"),
            "validation_status": validation.get("validation_status"),
        },
    )


def derive_ship_reliability(result: Dict[str, object]) -> Dict[str, object]:
    build_summary = dict(result.get("reliability_summary", {}))
    proof_result = dict(result.get("proof_result", {}))
    proof_artifacts = dict(proof_result.get("artifacts", {}))
    packaging = dict(result.get("packaged_app_artifact_summary", {}))
    deployment = dict(result.get("deployment_readiness_summary", {}))
    determinism_payload = dict(result.get("determinism", {}))

    proof_completeness = 1.0 if packaging.get("packaging_status") == "ready" else 0.6
    rollback_availability = 1.0 if proof_artifacts.get("artifact_paths", {}).get("proof_bundle") else 0.5
    determinism = 1.0 if determinism_payload.get("verified", False) else build_summary.get("components", {}).get("determinism", 0.0)
    reproducibility = 1.0 if proof_artifacts.get("artifact_paths", {}).get("replay_harness") else 0.5

    summary = build_reliability_summary(
        "ship",
        {
            "determinism": determinism,
            "repair_success": build_summary.get("components", {}).get("repair_success", 1.0),
            "proof_completeness": proof_completeness,
            "validation_completeness": 1.0 if result.get("validation_result", {}).get("status") == "passed" else 0.0,
            "rollback_availability": rollback_availability,
            "unsupported_feature_handling": build_summary.get("components", {}).get("unsupported_feature_handling", 1.0),
            "reproducibility": reproducibility,
        },
        proven=list(build_summary.get("proven", [])) + [
            f"deployment readiness status: {deployment.get('status', 'unknown')}",
            f"packaging status: {packaging.get('packaging_status', 'unknown')}",
        ],
        repaired=list(build_summary.get("repaired", [])),
        remaining_risks=list(build_summary.get("remaining_risks", [])),
        unsupported=list(build_summary.get("unsupported", [])),
        reproducibility_notes=list(build_summary.get("reproducibility_notes", [])),
        evidence={
            "proof_status": proof_result.get("status"),
            "deployment_status": deployment.get("status"),
            "packaging_status": packaging.get("packaging_status"),
        },
    )
    return summary