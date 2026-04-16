from planner.task import Task
from validator.confidence import calculate_confidence


def test_confidence_score_bounds():
    tasks = [Task(task_id="task-1", title="Analyze goal", status="complete")]
    score = calculate_confidence(tasks, {"status": "pass"}, 0)

    assert 0.0 <= score <= 1.0


def test_repair_lowers_confidence():
    tasks = [Task(task_id="task-1", title="Analyze goal", status="complete")]
    perfect_score = calculate_confidence(tasks, {"status": "pass"}, 0)
    repaired_score = calculate_confidence(tasks, {"status": "pass"}, 1)

    assert repaired_score < perfect_score
