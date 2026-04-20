from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def compute_claim(scorecard_path: str = "artifacts/benchmark_scorecard.json", coverage_path: str = "claims/coverage_matrix.json") -> Dict:
    score = json.loads(Path(scorecard_path).read_text())
    coverage = json.loads(Path(coverage_path).read_text())

    pass_rate = score.get("pass_rate", 0.0)
    supported = len(coverage.get("supported_app_classes", []))
    unsupported = len(coverage.get("unsupported_app_classes", []))

    coverage_ratio = supported / (supported + unsupported) if (supported + unsupported) else 0

    claim_valid = pass_rate >= 0.75 and coverage_ratio >= 0.5

    return {
        "pass_rate": pass_rate,
        "coverage_ratio": coverage_ratio,
        "claim_valid": claim_valid,
        "claim": "valid" if claim_valid else "not_valid",
    }
