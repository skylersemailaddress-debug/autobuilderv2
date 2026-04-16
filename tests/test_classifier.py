import pytest
from planner.task import Task
from debugger.classifier import FailureClassifier
from debugger.failures import FailureRecord


class TestFailureClassifier:
    def test_classify_task_execution_failure(self):
        classifier = FailureClassifier()
        task = Task(task_id="test-1", title="Test task", status="failed")
        
        result = classifier.classify(task)
        
        assert isinstance(result, FailureRecord)
        assert result.failure_type == "execution_failure"
        assert result.severity == "high"
        assert result.task_id == "test-1"
        assert result.recoverable is True
        assert result.replayable is True
        assert result.replay_case is not None
        assert result.benchmark_case is not None
        assert "Test task" in result.message

    def test_classify_task_missing_artifact(self):
        classifier = FailureClassifier()
        task = Task(task_id="test-2", title="Missing artifact task", status="pending", result=None)
        
        result = classifier.classify(task)
        
        assert isinstance(result, FailureRecord)
        assert result.failure_type == "missing_artifact"
        assert result.severity == "medium"
        assert result.task_id == "test-2"
        assert result.recoverable is True

    def test_classify_validation_failure(self):
        classifier = FailureClassifier()
        validation_result = {
            "status": "fail",
            "failed_tasks": ["task-1", "task-2"],
            "reason": "Some tasks are not complete",
            "evidence_type": "validation_result"
        }
        
        result = classifier.classify(validation_result)
        
        assert isinstance(result, FailureRecord)
        assert result.failure_type == "validation_failure"
        assert result.severity == "medium"
        assert "2 tasks incomplete" in result.message
        assert result.replay_case["expected_outcome"] == "repair_then_validate"

    def test_classify_task_list_with_policy_block(self):
        classifier = FailureClassifier()
        tasks = [
            Task(task_id="task-1", title="Policy blocked", status="failed", 
                 result={"error": "Policy violation: high risk action"}),
            Task(task_id="task-2", title="Normal task", status="complete")
        ]
        
        result = classifier.classify(tasks)
        
        assert isinstance(result, FailureRecord)
        assert result.failure_type == "policy_block"
        assert result.severity == "critical"
        assert result.recoverable is False

    def test_classify_task_list_execution_failure(self):
        classifier = FailureClassifier()
        tasks = [
            Task(task_id="task-1", title="Failed task", status="failed"),
            Task(task_id="task-2", title="Another failed", status="failed")
        ]
        
        result = classifier.classify(tasks)
        
        assert isinstance(result, FailureRecord)
        assert result.failure_type == "execution_failure"
        assert result.severity == "high"
        assert "2 tasks failed" in result.message

    def test_classify_unknown_failure(self):
        classifier = FailureClassifier()
        
        result = classifier.classify("unknown evidence type")
        
        assert isinstance(result, FailureRecord)
        assert result.failure_type == "unknown_failure"
        assert result.severity == "medium"
        assert "Unknown failure type" in result.message

    def test_failure_record_has_unique_id(self):
        classifier = FailureClassifier()
        task = Task(task_id="test", title="Test", status="failed")
        
        result1 = classifier.classify(task)
        result2 = classifier.classify(task)
        
        assert result1.failure_id != result2.failure_id
        assert result1.failure_id is not None
        assert result2.failure_id is not None