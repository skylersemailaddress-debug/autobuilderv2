from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Dict


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
    missing = [p for p in REQUIRED_EVIDENCE if not Path(p).exists()]
    return {"ok": not missing, "missing": missing}


def _validate_claim_alignment() -> Dict[str, Any]:
    path = Path("claims/coverage_matrix.json")
    if not path.exists():
        return {"ok": False, "error": "missing coverage matrix"}
    data = json.loads(path.read_text(encoding="utf-8"))
    supported = data.get("supported_app_classes", [])
    unsupported = data.get("unsupported_app_classes", [])
    claim = data.get("target_claim")
    if claim == "99_percent_of_apps" and len(supported) < 20:
        return {"ok": False, "error": "99_percent_of_apps claim unsupported by breadth of supported matrix"}
    return {"ok": True, "supported_count": len(supported), "unsupported_count": len(unsupported), "claim": claim}


def run() -> dict:
    report: Dict[str, Any] = {
        "validators": {},
        "evidence": {},
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
        report["errors"].append("required evidence artifacts missing")

    claim_alignment = _validate_claim_alignment()
    report["claim_alignment"] = claim_alignment
    if not claim_alignment.get("ok"):
        report["errors"].append(f"claim alignment failed: {claim_alignment.get('error')}")

    report["ready"] = not report["errors"]
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run()
