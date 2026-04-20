from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from benchmarks.enterprise_cases import run_enterprise_case
from benchmarks.execution_cases import run_execution_case
from benchmarks.recovery_cases import run_recovery_case
from benchmarks.scorecard import BenchmarkResult, summarize
from benchmarks.security_cases import run_security_case


def run_all() -> dict:
    results = [
        BenchmarkResult(
            "enterprise",
            run_enterprise_case({"app_name": "demo", "stack": "web", "status": "ready"}),
            {"kind": "enterprise"},
        ),
        BenchmarkResult(
            "security",
            run_security_case({"auth_enforced": True, "secrets_exposed": False}),
            {"kind": "security"},
        ),
        BenchmarkResult(
            "recovery",
            run_recovery_case(),
            {"kind": "recovery"},
        ),
        BenchmarkResult(
            "execution",
            run_execution_case(),
            {"kind": "execution"},
        ),
    ]
    return summarize(results)


def write_scorecard(output_path: str = "artifacts/benchmark_scorecard.json") -> Dict[str, Any]:
    scorecard = run_all()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scorecard, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return scorecard
