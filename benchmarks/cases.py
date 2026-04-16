from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    goal: str
    expected_outcome: Dict[str, Any]
    nexus_mode_enabled: bool = False
    requires_resume: bool = False
    auto_approve_on_resume: bool = False


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
        name="repair_required_mission",
        goal="Build an autonomous execution plan with strict validation",
        expected_outcome={
            "final_status": "complete",
            "minimum_repair_count": 1,
        },
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
]
