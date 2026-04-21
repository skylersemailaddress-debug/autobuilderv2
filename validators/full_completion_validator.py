from __future__ import annotations

import json
from pathlib import Path


def run() -> dict:
    result = {
        "supported_matrix_exists": Path("claims/coverage_matrix.json").exists(),
        "evidence_bundle_exists": Path("artifacts").exists(),
        "validators_exist": Path("validators/repo_completion_validator.py").exists(),
        "ci_workflow_exists": Path(".github/workflows/strict-validators.yml").exists(),
        "errors": [],
    }

    if not result["supported_matrix_exists"]:
        result["errors"].append("missing supported app coverage matrix")
    if not result["evidence_bundle_exists"]:
        result["errors"].append("missing artifacts directory")
    if not result["validators_exist"]:
        result["errors"].append("missing core validator suite")
    if not result["ci_workflow_exists"]:
        result["errors"].append("missing strict validator CI workflow")

    result["ready"] = not result["errors"]
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
