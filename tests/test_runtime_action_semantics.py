"""
Tests for runtime/action intelligence: task decomposition, state transitions,
evidence-of-success semantics, blocked/error/complete distinctions, escalation.
"""
import pytest
from planner.planner import Planner, _infer_decomposition, _DEFAULT_TASKS
from planner.task import Task
from execution.executor import Executor, _classify_action, _evidence_signature


# ---------------------------------------------------------------------------
# Planner: goal decomposition
# ---------------------------------------------------------------------------

def test_planner_decomposition_delete_goal():
    planner = Planner()
    result = planner.create_plan("Delete the user data table")
    tasks = result["tasks"]
    titles_lower = [t.title.lower() for t in tasks]
    # Should have more than 3 tasks for destructive goal
    assert len(tasks) >= 4
    meta = result["metadata"]
    assert meta["decomposition_strategy"] == "goal_based"
    assert "destructive" in meta["action_classes"]


def test_planner_decomposition_validate_goal():
    planner = Planner()
    result = planner.create_plan("Validate and proof the generated app")
    tasks = result["tasks"]
    assert len(tasks) >= 3
    meta = result["metadata"]
    assert "validation" in meta["action_classes"]


def test_planner_decomposition_update_goal():
    planner = Planner()
    result = planner.create_plan("Update the configuration file with new settings")
    tasks = result["tasks"]
    assert len(tasks) >= 3
    meta = result["metadata"]
    assert "mutation" in meta["action_classes"]


def test_planner_decomposition_build_goal():
    planner = Planner()
    result = planner.create_plan("Build a new SaaS application")
    tasks = result["tasks"]
    assert len(tasks) >= 3
    meta = result["metadata"]
    assert meta["decomposition_strategy"] == "goal_based"
    assert "creation" in meta["action_classes"]


def test_planner_plan_signature_deterministic():
    planner = Planner()
    r1 = planner.create_plan("Build a monitoring dashboard")
    r2 = planner.create_plan("Build a monitoring dashboard")
    assert r1["metadata"]["plan_signature"] == r2["metadata"]["plan_signature"]


def test_planner_plan_signature_differs_for_different_goals():
    planner = Planner()
    r1 = planner.create_plan("Build a monitoring dashboard")
    r2 = planner.create_plan("Delete production resources")
    assert r1["metadata"]["plan_signature"] != r2["metadata"]["plan_signature"]


def test_planner_default_fallback():
    planner = Planner()
    result = planner.create_plan("Xyzzy something completely unrecognized frob")
    assert len(result["tasks"]) == len(_DEFAULT_TASKS)
    assert result["metadata"]["decomposition_strategy"] == "default"


def test_planner_migrate_decomposition():
    specs = _infer_decomposition("Migrate database schema to new version")
    kinds = [s[1] for s in specs]
    assert "read" in kinds
    assert "mutation" in kinds
    assert "validation" in kinds


# ---------------------------------------------------------------------------
# Executor: state transitions and evidence semantics
# ---------------------------------------------------------------------------

def test_executor_basic_complete():
    executor = Executor()
    tasks = [Task(task_id="t1", title="Generate artifact"), Task(task_id="t2", title="Validate output")]
    result = executor.run_tasks(tasks)
    for t in result:
        assert t.status == "complete"
        assert t.result["execution_state"] == "complete"
        assert t.result["proof_ready"] is True


def test_executor_evidence_signature_present():
    executor = Executor()
    tasks = [Task(task_id="ev1", title="Build feature module")]
    executor.run_tasks(tasks)
    evidence = tasks[0].result["evidence_summary"]
    assert "evidence_signature" in evidence
    assert len(evidence["evidence_signature"]) == 16


def test_executor_action_class_classified():
    executor = Executor()
    tasks = [
        Task(task_id="c1", title="Delete old records from database"),
        Task(task_id="c2", title="Validate schema integrity"),
        Task(task_id="c3", title="Analyze repository structure"),
    ]
    executor.run_tasks(tasks)
    assert tasks[0].result["action_class"] == "destructive"
    assert tasks[1].result["action_class"] == "validation"
    assert tasks[2].result["action_class"] == "read"


def test_executor_blocked_task_skipped():
    executor = Executor()
    task = Task(task_id="b1", title="Blocked task")
    task.status = "blocked"
    executor.run_tasks([task])
    assert task.status == "blocked"
    assert task.result["execution_state"] == "blocked"
    assert "escalation" in task.result


def test_executor_recovery_no_failure():
    executor = Executor()
    tasks = [Task(task_id="r1", title="Build and validate")]
    result = executor.run_tasks_with_recovery(tasks)
    assert result[0].status == "complete"


def test_executor_evidence_deterministic():
    sig1 = _evidence_signature("t1", "Build feature", "complete")
    sig2 = _evidence_signature("t1", "Build feature", "complete")
    assert sig1 == sig2
    sig3 = _evidence_signature("t1", "Build feature", "error")
    assert sig1 != sig3


def test_executor_classify_action_destructive():
    assert _classify_action("Delete all users") == "destructive"
    assert _classify_action("Destroy the session cache") == "destructive"


def test_executor_classify_action_validation():
    assert _classify_action("Validate generated artifact") == "validation"
    assert _classify_action("Check contract integrity") == "validation"


def test_executor_classify_action_creation():
    assert _classify_action("Build new module") == "creation"
