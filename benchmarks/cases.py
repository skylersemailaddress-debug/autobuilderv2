from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    goal: str
    expected_outcome: Dict[str, Any]
    nexus_mode_enabled: bool = False


BENCHMARK_CASES: List[BenchmarkCase] = [
    BenchmarkCase(
        name="simple_run",
        goal="Build an autonomous execution plan",
        expected_outcome={
            "final_status": "complete",
            "approval_required": False,
        },
    ),
    BenchmarkCase(
        name="repair_run",
        goal="Build an autonomous execution plan with strict validation",
        expected_outcome={
            "final_status": "complete",
            "minimum_repair_count": 1,
        },
    ),
    BenchmarkCase(
        name="approval_run",
        goal="Delete production resources safely",
        expected_outcome={
            "final_status": "awaiting_approval",
            "approval_required": True,
        },
    ),
    BenchmarkCase(
        name="nexus_run",
        goal="Build an autonomous execution plan in Nexus mode",
        expected_outcome={
            "final_status": "complete",
            "nexus_mode": True,
        },
        nexus_mode_enabled=True,
    ),
]
