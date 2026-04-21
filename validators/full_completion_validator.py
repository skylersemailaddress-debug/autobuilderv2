from __future__ import annotations

import importlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List


STRICT_VALIDATORS = [
    "validators.repo_completion_validator",
    "validators.runtime_execution_validator",
    "validators.build_validator",
    "validators.release_validator",
    "validators.enforcement_validator",
    "validators.security_validator",
]

REQUIRED_EVIDENCE = [
    "claims/coverage_matrix.json",
    "artifacts/benchmark_scorecard.json",
    "generated_apps/latest.zip",
    ".github/workflows/strict-validators.yml",
]

MAX_EVIDENCE_AGE_SECONDS = 60 * 60 * 24

DEFAULT_CLASS_SPECS = {
    "crud_saas": {"app": {"type": "web_app", "features": ["authentication", "billing", "dashboard"]}, "stack": ["react", "fastapi", "postgres"]},
    "internal_dashboard": {"app": {"type": "dashboard_app", "features": ["dashboard", "admin_panel"]}, "stack": ["react", "fastapi"]},
    "content_site": {"app": {"type": "web_app", "features": ["authentication"]}, "stack": ["react", "fastapi"]},
    "api_service": {"app": {"type": "api_app", "features": ["api"]}, "stack": ["fastapi"]},
    "admin_portal": {"app": {"type": "dashboard_app", "features": ["admin_panel", "authentication"]}, "stack": ["react", "fastapi"]},
}


def _run_validator(module_name: str) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(module_name)
        if not hasattr(mod, "run"):
            return {"ok": False, "error": f"{module_name} missing run()"}
        result = mod.run()
        ready = bool(result.get("ready", False)) if isinstance(result, dict) else False
        return {"ok": ready, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _validate_evidence() -> Dict[str, Any]:
    now = time.time()
    missing = [p for p in REQUIRED_EVIDENCE if not Path(p).exists()]
    stale: List[str] = []
    for p in REQUIRED_EVIDENCE:
        path = Path(p)
        if path.exists() and (now - path.stat().st_mtime) > MAX_EVIDENCE_AGE_SECONDS:
            stale.append(p)
    return {"ok": not missing and not stale, "missing": missing, "stale": stale}


def _run_supported_matrix() -> Dict[str, Any]:
    try:
        coverage = json.loads(Path("claims/coverage_matrix.json").read_text(encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"unable to load coverage matrix: {e}"}

    supported = coverage.get("supported_app_classes", [])
    class_results: Dict[str, Any] = {}
    failures: List[str] = []

    try:
        from chat_build.output_lane import generate_app_from_spec, validate_generated_output
    except Exception as e:
        return {"ok": False, "error": f"output lane unavailable: {e}"}

    for app_class in supported:
        spec = DEFAULT_CLASS_SPECS.get(app_class)
        if spec is None:
            failures.append(app_class)
            class_results[app_class] = {"ok": False, "error": "no execution spec available for supported class"}
            continue
        try:
            output = generate_app_from_spec(spec)
            validation = validate_generated_output(output["root"]) if isinstance(output, dict) and output.get("root") else {"valid": False}
            ok = bool(isinstance(output, dict) and output.get("package") and validation.get("valid"))
            class_results[app_class] = {"ok": ok, "output_root": output.get("root") if isinstance(output, dict) else None, "validation": validation}
            if not ok:
                failures.append(app_class)
        except Exception as e:
            failures.append(app_class)
            class_results[app_class] = {"ok": False, "error": str(e)}

    success_rate = ((len(supported) - len(failures)) / len(supported)) if supported else 0.0
    return {"ok": not failures, "success_rate": success_rate, "class_results": class_results, "failures": failures}


def _validate_claim_alignment(matrix_result: Dict[str, Any]) -> Dict[str, Any]:
    path = Path("claims/coverage_matrix.json")
    if not path.exists():
        return {"ok": False, "error": "missing coverage matrix"}
    data = json.loads(path.read_text(encoding="utf-8"))
    supported = data.get("supported_app_classes", [])
    unsupported = data.get("unsupported_app_classes", [])
    claim = data.get("target_claim")

    success_rate = float(matrix_result.get("success_rate", 0.0))
    if claim == "99_percent_of_apps" and success_rate < 0.99:
        return {"ok": False, "error": f"99_percent_of_apps claim unsupported by measured success_rate={success_rate}"}

    return {
        "ok": True,
        "supported_count": len(supported),
        "unsupported_count": len(unsupported),
        "claim": claim,
        "measured_success_rate": success_rate,
    }


def run() -> dict:
    report: Dict[str, Any] = {
        "validators": {},
        "evidence": {},
        "supported_matrix_execution": {},
        "claim_alignment": {},
        "errors": [],
    }

    for module_name in STRICT_VALIDATORS:
        outcome = _run_validator(module_name)
        report["validators"][module_name] = outcome
        if not outcome.get("ok"):
            report["errors"].append(f"validator failed: {module_name}")

    evidence = _validate_evidence()
    report["evidence"] = evidence
    if not evidence.get("ok"):
        if evidence.get("missing"):
            report["errors"].append("required evidence artifacts missing")
        if evidence.get("stale"):
            report["errors"].append("required evidence artifacts are stale")

    matrix_result = _run_supported_matrix()
    report["supported_matrix_execution"] = matrix_result
    if not matrix_result.get("ok"):
        report["errors"].append("supported app-class matrix execution failed")

    claim_alignment = _validate_claim_alignment(matrix_result)
    report["claim_alignment"] = claim_alignment
    if not claim_alignment.get("ok"):
        report["errors"].append(f"claim alignment failed: {claim_alignment.get('error')}")

    report["ready"] = not report["errors"]
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run()
