import tempfile
from pathlib import Path
import json
from state.resume_runner import infer_next_stage, resume_run


def test_infer_next_stage_plan():
    """Test inferring planning stage when no tasks exist."""
    record = {"tasks": []}
    assert infer_next_stage(record) == "plan"


def test_infer_next_stage_execute():
    """Test inferring execution stage when tasks are incomplete."""
    record = {
        "tasks": [
            {"task_id": "task-1", "status": "complete"},
            {"task_id": "task-2", "status": "pending"}
        ]
    }
    assert infer_next_stage(record) == "execute"


def test_infer_next_stage_repair():
    """Test inferring repair stage when validation failed and retry available."""
    record = {
        "tasks": [
            {"task_id": "task-1", "status": "complete"},
            {"task_id": "task-2", "status": "complete"}
        ],
        "validation_result": {"status": "fail"},
        "repair_count": 0
    }
    assert infer_next_stage(record) == "repair"


def test_infer_next_stage_complete():
    """Test no action needed when run is complete."""
    record = {
        "tasks": [
            {"task_id": "task-1", "status": "complete"},
            {"task_id": "task-2", "status": "complete"}
        ],
        "validation_result": {"status": "pass"}
    }
    assert infer_next_stage(record) is None


def test_infer_next_stage_failed():
    """Test no action possible when run has failed."""
    record = {
        "tasks": [
            {"task_id": "task-1", "status": "complete"},
            {"task_id": "task-2", "status": "complete"}
        ],
        "validation_result": {"status": "fail"},
        "repair_count": 1  # Max repairs reached
    }
    assert infer_next_stage(record) is None


def test_resume_run_marks_resumed():
    """Test that resume_run marks the record as resumed."""
    record = {
        "run_id": "test-run",
        "tasks": [{"task_id": "task-1", "status": "pending"}]
    }
    
    resumed = resume_run(record)
    
    assert resumed["resumed"] is True
    assert resumed["resumed_from"] == "execute"
