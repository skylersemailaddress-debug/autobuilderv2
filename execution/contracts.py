from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ArtifactContract:
    artifact_type: str
    required_fields: List[str]
    allowed_fields: List[str]

    def validate(self, artifact: Dict) -> Dict:
        missing_fields = [field for field in self.required_fields if field not in artifact]
        invalid_fields = [field for field in artifact if field not in self.allowed_fields]
        return {
            "artifact_type": self.artifact_type,
            "required_fields": self.required_fields,
            "allowed_fields": self.allowed_fields,
            "missing_fields": missing_fields,
            "invalid_fields": invalid_fields,
            "passed": not missing_fields,
        }


PLAN_CONTRACT = ArtifactContract(
    artifact_type="plan",
    required_fields=["goal", "task_count", "memory_used", "repo_mode", "repo_signals"],
    allowed_fields=[
        "goal",
        "task_count",
        "memory_used",
        "memory_insights",
        "repo_mode",
        "repo_signals",
    ],
)

TASK_RESULT_CONTRACT = ArtifactContract(
    artifact_type="task_result",
    required_fields=["artifact_id", "artifact_type", "content", "created_at"],
    allowed_fields=["artifact_id", "artifact_type", "content", "created_at"],
)

RUN_SUMMARY_CONTRACT = ArtifactContract(
    artifact_type="run_summary",
    required_fields=[
        "run_id",
        "goal",
        "final_status",
        "total_tasks",
        "completed_tasks",
        "event_count",
        "confidence",
        "checkpoint_count",
        "artifact_count",
        "risk_level",
        "approval_required",
        "awaiting_approval",
        "control_state",
        "memory_used",
        "memory_hits",
        "failure_count",
        "failure_types",
        "critical_failures",
        "repo_mode",
        "repo_signals",
    ],
    allowed_fields=[
        "run_id",
        "goal",
        "final_status",
        "total_tasks",
        "completed_tasks",
        "event_count",
        "confidence",
        "checkpoint_count",
        "artifact_count",
        "risk_level",
        "approval_required",
        "awaiting_approval",
        "control_state",
        "repair_used",
        "repair_count",
        "contract_validation_passed",
        "project_name",
        "nexus_mode",
        "approvals_enabled",
        "resumability_enabled",
        "memory_used",
        "memory_hits",
        "failure_count",
        "failure_types",
        "critical_failures",
        "repo_mode",
        "repo_signals",
    ],
)

CONTRACTS = {
    "plan": PLAN_CONTRACT,
    "task_result": TASK_RESULT_CONTRACT,
    "run_summary": RUN_SUMMARY_CONTRACT,
}
