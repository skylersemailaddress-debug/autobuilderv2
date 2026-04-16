from planner.task import Task
from validator.validator import Validator


def test_validator_passes_when_tasks_complete():
    tasks = [
        Task(task_id="task-1", title="Analyze goal", status="complete", result={}),
        Task(task_id="task-2", title="Generate artifact", status="complete", result={}),
    ]
    validator = Validator()

    success, evidence = validator.validate(tasks)

    assert success is True
    assert evidence["status"] == "pass"


def test_validator_fails_when_any_task_pending():
    tasks = [
        Task(task_id="task-1", title="Analyze goal", status="complete", result={}),
        Task(task_id="task-2", title="Generate artifact", status="pending"),
    ]
    validator = Validator()

    success, evidence = validator.validate(tasks)

    assert success is False
    assert evidence["status"] == "fail"
    assert evidence["failed_tasks"] == ["task-2"]
    assert "reason" in evidence
