from pathlib import Path
from typing import Dict, List, Tuple


ROOT_DIR = Path(__file__).resolve().parents[1]


def _check_file_exists(name: str, relative_path: str) -> Dict:
    path = ROOT_DIR / relative_path
    passed = path.exists()
    return {
        "name": name,
        "passed": passed,
        "path": relative_path,
        "details": "present" if passed else "missing",
    }


def run_readiness_checks() -> Dict:
    checks = [
        _check_file_exists("mission_runner_present", "cli/mission.py"),
        _check_file_exists("resume_path_present", "cli/resume.py"),
        _check_file_exists("inspect_path_present", "cli/inspect.py"),
        _check_file_exists("benchmark_harness_present", "benchmarks/runner.py"),
        _check_file_exists("mutation_safety_present", "mutation/safety.py"),
        _check_file_exists("restore_support_present", "state/restore.py"),
        _check_file_exists("memory_policy_present", "memory/policy.py"),
        _check_file_exists("quality_reporting_present", "quality/report.py"),
    ]
    passed_count = sum(1 for item in checks if item["passed"])
    return {
        "checks": checks,
        "passed_count": passed_count,
        "failed_count": len(checks) - passed_count,
        "total_checks": len(checks),
        "all_passed": passed_count == len(checks),
    }
