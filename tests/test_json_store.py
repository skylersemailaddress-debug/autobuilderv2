import json
from pathlib import Path
import uuid

from state.json_store import JsonRunStore


def test_json_store_roundtrip(tmp_path):
    store = JsonRunStore(base_dir=tmp_path)
    run_id = uuid.uuid4().hex
    record = {
        "run_id": run_id,
        "status": "complete",
        "state_history": ["intake", "plan", "execute", "validate", "complete"],
        "artifacts": [{"state": "complete"}],
        "validation_result": {"status": "pass"},
    }

    saved_path = store.save(run_id, record)
    assert saved_path.exists()
    loaded = store.load(run_id)

    assert loaded == record
    assert isinstance(loaded, dict)
    assert loaded["run_id"] == run_id
    assert loaded["status"] == "complete"
    assert loaded["state_history"][-1] == "complete"
