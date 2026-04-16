from state.restore import build_restore_payload, latest_restore_payload


def test_build_restore_payload_found_checkpoint():
    record = {
        "run_id": "run-1",
        "checkpoints": [
            {
                "checkpoint_id": "plan-abc",
                "stage": "plan",
                "metadata": {"task_count": 3},
            }
        ],
    }

    payload = build_restore_payload(record, "plan-abc")
    assert payload["run_id"] == "run-1"
    assert payload["checkpoint_id"] == "plan-abc"
    assert payload["stage"] == "plan"
    assert payload["metadata"]["task_count"] == 3
    assert payload["restore_possible"] is True
    assert payload["restore_plan"]["rollback_ready"] is True
    assert payload["failure_semantics"] == "resume_from_checkpoint"


def test_build_restore_payload_missing_checkpoint():
    record = {"run_id": "run-1", "checkpoints": []}
    payload = build_restore_payload(record, "missing")
    assert payload["run_id"] == "run-1"
    assert payload["checkpoint_id"] == "missing"
    assert payload["restore_possible"] is False
    assert payload["failure_semantics"] == "checkpoint_missing"


def test_latest_restore_payload():
    record = {
        "run_id": "run-1",
        "checkpoints": [
            {"checkpoint_id": "start-a", "stage": "start", "metadata": {}},
            {"checkpoint_id": "end-b", "stage": "complete", "metadata": {}},
        ],
    }
    payload = latest_restore_payload(record)
    assert payload is not None
    assert payload["checkpoint_id"] == "end-b"
    assert payload["restore_possible"] is True
    assert payload["restore_plan"]["strategy"] == "checkpoint_restore"
