import uuid
from typing import Dict, Any, Union, List
from planner.task import Task
from debugger.failures import FailureRecord


class FailureClassifier:
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
                recoverable=True
            )

    def _classify_task_failure(self, task: Task) -> FailureRecord:
        """Classify failure based on a single task."""
        if task.status == "failed":
            return self._create_failure_record(
                failure_type="execution_failure",
                severity="high",
                message=f"Task execution failed: {task.title}",
                task_id=task.task_id,
                recoverable=True
            )
        elif task.status == "pending" and task.result is None:
            return self._create_failure_record(
                failure_type="missing_artifact",
                severity="medium",
                message=f"Task missing expected artifact: {task.title}",
                task_id=task.task_id,
                recoverable=True
            )
        else:
            return self._create_failure_record(
                failure_type="unknown_failure",
                severity="low",
                message=f"Unexpected task state: {task.status} for {task.title}",
                task_id=task.task_id,
                recoverable=True
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
                    recoverable=True
                )
            else:
                return self._create_failure_record(
                    failure_type="validation_failure",
                    severity="high",
                    message=f"Validation failed: {reason}",
                    recoverable=True
                )
        else:
            return self._create_failure_record(
                failure_type="unknown_failure",
                severity="low",
                message="Validation result indicates no failure",
                recoverable=True
            )

    def _classify_task_list_failure(self, tasks: List[Task]) -> FailureRecord:
        """Classify failure based on a list of tasks."""
        failed_tasks = [task for task in tasks if task.status != "complete"]
        
        if not failed_tasks:
            return self._create_failure_record(
                failure_type="unknown_failure",
                severity="low",
                message="No failed tasks found in list",
                recoverable=True
            )
        
        # Check for policy-related failures
        policy_blocks = [task for task in failed_tasks if task.result and "policy" in str(task.result).lower()]
        if policy_blocks:
            return self._create_failure_record(
                failure_type="policy_block",
                severity="critical",
                message=f"Policy blocked {len(policy_blocks)} tasks",
                recoverable=False
            )
        
        # Default to execution failure
        return self._create_failure_record(
            failure_type="execution_failure",
            severity="high",
            message=f"{len(failed_tasks)} tasks failed execution",
            recoverable=True
        )

    def _create_failure_record(self, failure_type: str, severity: str, message: str, 
                             task_id: str = None, recoverable: bool = True) -> FailureRecord:
        """Create a standardized failure record."""
        return FailureRecord(
            failure_id=str(uuid.uuid4()),
            failure_type=failure_type,
            severity=severity,
            message=message,
            task_id=task_id,
            recoverable=recoverable
        )