import uuid
from typing import Dict, Any, Union, List
from planner.task import Task
from debugger.failures import FailureRecord


class FailureClassifier:
    def _build_replay_case(
        self,
        *,
        failure_type: str,
        evidence: Dict[str, Any],
        expected_outcome: str,
    ) -> Dict[str, object]:
        return {
            "case_type": "replayable_failure",
            "failure_type": failure_type,
            "expected_outcome": expected_outcome,
            "evidence": evidence,
        }

    def classify(self, evidence: Union[Task, Dict[str, Any], List[Task]]) -> FailureRecord:
        """Classify a failure based on task or validation evidence."""
        
        if isinstance(evidence, Task):
            return self._classify_task_failure(evidence)
        elif isinstance(evidence, dict):
            return self._classify_validation_failure(evidence)
        elif isinstance(evidence, list):
            return self._classify_task_list_failure(evidence)
        else:
            return self._create_failure_record(
                failure_type="unknown_failure",
                severity="medium",
                message=f"Unknown failure type: {type(evidence)}",
                recoverable=True,
                replay_case=self._build_replay_case(
                    failure_type="unknown_failure",
                    evidence={"python_type": str(type(evidence))},
                    expected_outcome="manual_review",
                ),
                benchmark_case={"name": "replay_unknown_failure", "kind": "failure_replay"},
            )

    def _classify_task_failure(self, task: Task) -> FailureRecord:
        """Classify failure based on a single task."""
        if task.status == "failed":
            return self._create_failure_record(
                failure_type="execution_failure",
                severity="high",
                message=f"Task execution failed: {task.title}",
                task_id=task.task_id,
                recoverable=True,
                replay_case=self._build_replay_case(
                    failure_type="execution_failure",
                    evidence={"task_id": task.task_id, "title": task.title, "status": task.status},
                    expected_outcome="repair_or_retry",
                ),
                benchmark_case={"name": "execution_failure_replay", "kind": "failure_replay"},
            )
        elif task.status == "pending" and task.result is None:
            return self._create_failure_record(
                failure_type="missing_artifact",
                severity="medium",
                message=f"Task missing expected artifact: {task.title}",
                task_id=task.task_id,
                recoverable=True,
                replay_case=self._build_replay_case(
                    failure_type="missing_artifact",
                    evidence={"task_id": task.task_id, "title": task.title},
                    expected_outcome="recreate_artifact",
                ),
                benchmark_case={"name": "missing_artifact_replay", "kind": "failure_replay"},
            )
        else:
            return self._create_failure_record(
                failure_type="unknown_failure",
                severity="low",
                message=f"Unexpected task state: {task.status} for {task.title}",
                task_id=task.task_id,
                recoverable=True,
                replay_case=self._build_replay_case(
                    failure_type="unknown_failure",
                    evidence={"task_id": task.task_id, "status": task.status, "title": task.title},
                    expected_outcome="manual_review",
                ),
                benchmark_case={"name": "task_state_replay", "kind": "failure_replay"},
            )

    def _classify_validation_failure(self, validation_result: Dict[str, Any]) -> FailureRecord:
        """Classify failure based on validation result."""
        status = validation_result.get("status")
        if status == "fail":
            failed_tasks = validation_result.get("failed_tasks", [])
            reason = validation_result.get("reason", "Unknown validation failure")
            
            if "not complete" in reason.lower():
                return self._create_failure_record(
                    failure_type="validation_failure",
                    severity="medium",
                    message=f"Validation failed: {len(failed_tasks)} tasks incomplete",
                    recoverable=True,
                    replay_case=self._build_replay_case(
                        failure_type="validation_failure",
                        evidence={
                            "failed_tasks": failed_tasks,
                            "failed_count": validation_result.get("failed_count", len(failed_tasks)),
                        },
                        expected_outcome="repair_then_validate",
                    ),
                    benchmark_case={"name": "validation_failure_replay", "kind": "failure_replay"},
                )
            else:
                return self._create_failure_record(
                    failure_type="validation_failure",
                    severity="high",
                    message=f"Validation failed: {reason}",
                    recoverable=True,
                    replay_case=self._build_replay_case(
                        failure_type="validation_failure",
                        evidence=validation_result,
                        expected_outcome="repair_then_validate",
                    ),
                    benchmark_case={"name": "validation_failure_replay", "kind": "failure_replay"},
                )
        else:
            return self._create_failure_record(
                failure_type="unknown_failure",
                severity="low",
                message="Validation result indicates no failure",
                recoverable=True,
                replay_case=self._build_replay_case(
                    failure_type="unknown_failure",
                    evidence=validation_result,
                    expected_outcome="manual_review",
                ),
                benchmark_case={"name": "validation_unknown_replay", "kind": "failure_replay"},
            )

    def _classify_task_list_failure(self, tasks: List[Task]) -> FailureRecord:
        """Classify failure based on a list of tasks."""
        failed_tasks = [task for task in tasks if task.status != "complete"]
        
        if not failed_tasks:
            return self._create_failure_record(
                failure_type="unknown_failure",
                severity="low",
                message="No failed tasks found in list",
                recoverable=True,
                replay_case=self._build_replay_case(
                    failure_type="unknown_failure",
                    evidence={"task_count": len(tasks)},
                    expected_outcome="manual_review",
                ),
                benchmark_case={"name": "empty_failure_list_replay", "kind": "failure_replay"},
            )
        
        # Check for policy-related failures
        policy_blocks = [task for task in failed_tasks if task.result and "policy" in str(task.result).lower()]
        if policy_blocks:
            return self._create_failure_record(
                failure_type="policy_block",
                severity="critical",
                message=f"Policy blocked {len(policy_blocks)} tasks",
                recoverable=False,
                replay_case=self._build_replay_case(
                    failure_type="policy_block",
                    evidence={"blocked_tasks": [task.task_id for task in policy_blocks]},
                    expected_outcome="approval_pause",
                ),
                benchmark_case={"name": "policy_block_replay", "kind": "failure_replay"},
            )
        
        # Default to execution failure
        return self._create_failure_record(
            failure_type="execution_failure",
            severity="high",
            message=f"{len(failed_tasks)} tasks failed execution",
            recoverable=True,
            replay_case=self._build_replay_case(
                failure_type="execution_failure",
                evidence={"failed_tasks": [task.task_id for task in failed_tasks]},
                expected_outcome="repair_or_retry",
            ),
            benchmark_case={"name": "task_list_execution_failure_replay", "kind": "failure_replay"},
        )

    def _create_failure_record(self, failure_type: str, severity: str, message: str, 
                             task_id: str = None, recoverable: bool = True,
                             replay_case: Dict[str, object] | None = None,
                             benchmark_case: Dict[str, object] | None = None) -> FailureRecord:
        """Create a standardized failure record."""
        return FailureRecord(
            failure_id=str(uuid.uuid4()),
            failure_type=failure_type,
            severity=severity,
            message=message,
            task_id=task_id,
            recoverable=recoverable,
            replayable=True,
            replay_case=replay_case,
            benchmark_case=benchmark_case,
        )