from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    expected_outcome: Dict[str, Any]
    goal: str = ""
    kind: str = "mission"
    nexus_mode_enabled: bool = False
    requires_resume: bool = False
    auto_approve_on_resume: bool = False
    spec_path: str | None = None
    requested_capabilities: list[str] | None = None
    approve_core: bool = False


BENCHMARK_CASES: List[BenchmarkCase] = [
    BenchmarkCase(
        name="simple_low_risk_mission",
        goal="Build an autonomous execution plan",
        expected_outcome={
            "final_status": "complete",
            "approval_required": False,
        },
    ),
    BenchmarkCase(
        name="repair_retry_generated_app",
        expected_outcome={
            "validation_status": "passed",
            "minimum_repair_count": 1,
        },
        kind="repair_flow",
    ),
    BenchmarkCase(
        name="approval_required_dangerous_mission",
        goal="Delete production resources safely",
        expected_outcome={
            "final_status": "awaiting_approval",
            "approval_required": True,
        },
    ),
    BenchmarkCase(
        name="repo_targeted_mission",
        goal="Update repository config and improve test coverage",
        expected_outcome={
            "final_status": "complete",
            "repo_mode": True,
        },
    ),
    BenchmarkCase(
        name="nexus_mission_mode_run",
        goal="Build an autonomous execution plan in Nexus mode",
        expected_outcome={
            "final_status": "complete",
            "nexus_mode": True,
        },
        nexus_mode_enabled=True,
    ),
    BenchmarkCase(
        name="interrupted_resumable_mission",
        goal="Delete production resources safely",
        expected_outcome={
            "final_status": "complete",
            "approval_required": True,
            "resumed": True,
        },
        nexus_mode_enabled=True,
        requires_resume=True,
        auto_approve_on_resume=True,
    ),
    BenchmarkCase(
        name="first_class_ship_flow",
        expected_outcome={
            "build_status": "ok",
            "proof_status_prefix": "certified",
            "packaging_status": "ready",
        },
        kind="ship",
        spec_path="specs",
    ),
    BenchmarkCase(
        name="unsupported_feature_rejection",
        expected_outcome={
            "error_contains": "Unsupported",
            "unsupported_handled": True,
        },
        kind="unsupported_build",
    ),
    BenchmarkCase(
        name="self_extension_validation_scenario",
        expected_outcome={
            "status": "extended",
            "registered": True,
        },
        kind="self_extend",
        requested_capabilities=["custom_validator_for_geo"],
        approve_core=True,
    ),
]
