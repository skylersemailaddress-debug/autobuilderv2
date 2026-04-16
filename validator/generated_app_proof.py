from __future__ import annotations

import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def emit_generated_app_proof_artifacts(
    target_repo: str | Path,
    build_status: str,
    validation_report: dict[str, object],
    determinism: dict[str, object],
    repair_report: dict[str, object],
) -> dict[str, object]:
    target = Path(target_repo).resolve()
    autobuilder_dir = target / ".autobuilder"

    validation_status = str(validation_report.get("validation_status", "failed"))
    blockers = repair_report.get("unrepaired_blockers", [])
    repaired = repair_report.get("repaired_issues", [])

    if validation_status == "passed" and not blockers:
        proof_status = "certified_with_repairs" if repaired else "certified"
    else:
        proof_status = "not_certified"

    proof_report = {
        "proof_status": proof_status,
        "build_status": build_status,
        "validation_status": validation_status,
        "failed_checks": validation_report.get("failed_checks", []),
        "repaired_issues": repaired,
        "unrepaired_blockers": blockers,
    }
    readiness_report = {
        "readiness_status": "ready" if proof_status.startswith("certified") else "not_ready",
        "readiness_reasons": [] if proof_status.startswith("certified") else ["generated app validation not certified"],
        "validation_status": validation_status,
    }
    validation_summary = {
        "validation_status": validation_status,
        "all_passed": validation_report.get("all_passed", False),
        "passed_count": validation_report.get("passed_count", 0),
        "failed_count": validation_report.get("failed_count", 0),
        "total_checks": validation_report.get("total_checks", 0),
        "failed_checks": validation_report.get("failed_checks", []),
    }
    determinism_signature = {
        "build_signature_sha256": determinism.get("build_signature_sha256", ""),
        "proof_signature_sha256": determinism.get("proof_signature_sha256", ""),
        "repeat_build_match_required": determinism.get("repeat_build_match_required", True),
        "verified": determinism.get("verified", False),
    }

    paths = {
        "proof_report": _write_json(autobuilder_dir / "proof_report.json", proof_report),
        "readiness_report": _write_json(autobuilder_dir / "readiness_report.json", readiness_report),
        "validation_summary": _write_json(autobuilder_dir / "validation_summary.json", validation_summary),
        "determinism_signature": _write_json(
            autobuilder_dir / "determinism_signature.json", determinism_signature
        ),
    }

    return {
        "proof_status": proof_status,
        "validation_status": validation_status,
        "artifact_paths": paths,
        "repaired_issues": repaired,
        "unrepaired_blockers": blockers,
    }
