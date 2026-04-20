from __future__ import annotations

from typing import Any, Dict


def build_release_scorecard(readiness: Dict[str, Any], benchmarks: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
    ready = bool(readiness.get("ready"))
    pass_rate = float(benchmarks.get("pass_rate", 0.0))
    valid = bool(validation.get("valid", False))
    launch_blocked = not (ready and valid and pass_rate >= 0.75)
    return {
        "ready": ready,
        "benchmark_pass_rate": pass_rate,
        "validation_passed": valid,
        "launch_blocked": launch_blocked,
        "status": "blocked" if launch_blocked else "launchable",
    }
