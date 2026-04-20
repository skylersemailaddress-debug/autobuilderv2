from __future__ import annotations

import importlib
import json
from pathlib import Path


def check_imports():
    modules = [
        "benchmarks.runner",
        "chat_build.output_lane",
        "commerce.entitlements.service",
        "self_extend.lifecycle",
    ]
    failures = []
    for m in modules:
        try:
            importlib.import_module(m)
        except Exception as e:
            failures.append((m, str(e)))
    return failures


def check_required_files():
    required = [
        "benchmarks/runner.py",
        "chat_build/output_lane.py",
        "ops/release_scorecard.py",
        "claims/validator.py",
    ]
    missing = [p for p in required if not Path(p).exists()]
    return missing


def check_artifacts():
    artifacts = [
        "artifacts/benchmark_scorecard.json",
        "generated_apps/latest.zip",
    ]
    missing = [p for p in artifacts if not Path(p).exists()]
    return missing


def run_validator():
    report = {
        "import_failures": check_imports(),
        "missing_files": check_required_files(),
        "missing_artifacts": check_artifacts(),
    }
    report["ready"] = not any(report.values())
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run_validator()
