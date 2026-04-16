from state.resume import resume_run


def test_resume_payload_shape():
    record = {
        "run_id": "run-123",
        "goal": "Build something",
        "status": "complete",
        "summary": {"total_tasks": 3},
        "memory_keys": ["goal", "summary"],
        "state_history": ["intake", "plan", "execute", "complete"],
        "repair_count": 1,
    }
    
    resume = resume_run(record)
    
    assert resume["run_id"] == "run-123"
    assert resume["goal"] == "Build something"
    assert resume["final_status"] == "complete"
    assert resume["summary"] == {"total_tasks": 3}
    assert resume["memory_keys"] == ["goal", "summary"]
    assert resume["last_state"] == "complete"
    assert resume["repair_count"] == 1


def test_resume_payload_empty_state_history():
    record = {
        "run_id": "run-456",
        "goal": "Test goal",
        "status": "failed",
        "summary": {},
        "memory_keys": [],
        "repair_count": 0,
    }
    
    resume = resume_run(record)
    
    assert resume["run_id"] == "run-456"
    assert resume["last_state"] is None
    assert resume["repair_count"] == 0
