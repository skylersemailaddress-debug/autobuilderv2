from state.restore import build_restore_payload, latest_restore_payload


def test_build_restore_payload_found_checkpoint():
    record = {
        "run_id": "run-1",
        "checkpoints": [
            {
                "checkpoint_id": "plan-abc",
                "stage": "plan",
                "metadata": {"task_count": 3},
                "manifest_version": "v3",
                "rollback_reference": "rollback:plan-abc",
                "restore_metadata": {"durable": True, "restorable": True},
                "failure_semantics": {"mode": "resume_from_checkpoint"},
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
    assert payload["restore_metadata"]["durable"] is True
    assert payload["failure_semantics"]["mode"] == "resume_from_checkpoint"
    assert payload["restore_references"]["manifest_version"] == "v3"


def test_build_restore_payload_missing_checkpoint():
    record = {"run_id": "run-1", "checkpoints": []}
    payload = build_restore_payload(record, "missing")
    assert payload["run_id"] == "run-1"
    assert payload["checkpoint_id"] == "missing"
    assert payload["restore_possible"] is False
    assert payload["failure_semantics"] == "checkpoint_missing"
    assert payload["restore_metadata"] == {}


def test_latest_restore_payload():
    record = {
        "run_id": "run-1",
        "checkpoints": [
            {"checkpoint_id": "start-a", "stage": "start", "metadata": {}},
            {
                "checkpoint_id": "end-b",
                "stage": "complete",
                "metadata": {},
                "restore_metadata": {"restorable": True},
            },
        ],
    }
    payload = latest_restore_payload(record)
    assert payload is not None
    assert payload["checkpoint_id"] == "end-b"
    assert payload["restore_possible"] is True
    assert payload["restore_plan"]["strategy"] == "checkpoint_restore"
