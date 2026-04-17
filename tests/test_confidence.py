from planner.task import Task
from validator.confidence import calculate_confidence, calculate_confidence_details


def test_confidence_score_bounds():
    tasks = [Task(task_id="task-1", title="Analyze goal", status="complete")]
    score = calculate_confidence(tasks, {"status": "pass"}, 0)

    assert 0.0 <= score <= 1.0


def test_repair_lowers_confidence():
    tasks = [Task(task_id="task-1", title="Analyze goal", status="complete")]
    perfect_score = calculate_confidence(tasks, {"status": "pass"}, 0)
    repaired_score = calculate_confidence(tasks, {"status": "pass"}, 1)

    assert repaired_score < perfect_score


def test_confidence_derivation_is_measurable_and_consistent():
    tasks = [
        Task(task_id="task-1", title="Analyze goal", status="complete"),
        Task(task_id="task-2", title="Execute plan", status="complete"),
    ]

    details = calculate_confidence_details(
        tasks,
        {"status": "pass"},
        1,
        contract_validation_passed=True,
        rollback_available=True,
        unsupported_feature_count=0,
        reproducible=True,
    )

    assert details["score"] == calculate_confidence(
        tasks,
        {"status": "pass"},
        1,
        contract_validation_passed=True,
        rollback_available=True,
        unsupported_feature_count=0,
        reproducible=True,
    )
    assert "task_completion" in details["components"]
    assert details["derived_from"]["completed_tasks"] == 2
    assert "measurable factors" in details["explanation"]
    assert details["derived_from"]["model_version"] == "v2"
    assert "formula" in details


def test_confidence_includes_determinism_and_reliability_alignment() -> None:
    tasks = [Task(task_id="task-1", title="Analyze goal", status="complete")]
    details = calculate_confidence_details(
        tasks,
        {"status": "pass"},
        0,
        determinism_verified=True,
        reliability_score=0.95,
    )

    assert "determinism" in details["components"]
    assert "reliability_alignment" in details["components"]
    assert details["components"]["determinism"] == 1.0
    assert details["components"]["reliability_alignment"] == 0.95
