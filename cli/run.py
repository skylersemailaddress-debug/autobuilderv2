import sys
from pathlib import Path
from datetime import datetime, timezone
import uuid
import json

# Ensure top-level package imports work when executing cli/run.py directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from orchestrator.run_state_machine import RunStateMachine, RunState
from state.run_state import RunStateStore
from state.json_store import JsonRunStore
from validator.validator import Validator


def perform_run(run_id):
    created_at = datetime.now(timezone.utc).isoformat()
    state_store = RunStateStore()
    run_sm = RunStateMachine()
    validator = Validator()
    json_store = JsonRunStore(base_dir=ROOT_DIR / "runs")

    history = [run_sm.state.value]
    state_store.save(run_id, run_sm.state.value)
    artifacts = [{"state": run_sm.state.value, "timestamp": created_at}]
    validation_result = None

    while run_sm.state not in (RunState.COMPLETE, RunState.FAILED):
        if run_sm.state == RunState.VALIDATE:
            success, validation_result = validator.validate({"run_id": run_id})
            next_state = run_sm.transition(success=success)
        else:
            next_state = run_sm.transition(success=True)

        state_store.save(run_id, next_state.value)
        history.append(next_state.value)
        artifacts.append(
            {
                "state": next_state.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        if next_state == RunState.FAILED:
            break

    status = run_sm.state.value
    record = {
        "run_id": run_id,
        "created_at": created_at,
        "status": status,
        "state_history": history,
        "artifacts": artifacts,
        "validation_result": validation_result,
    }
    saved_path = json_store.save(run_id, record)

    print(f"run_id={run_id}")
    print(f"status={status}")
    print(f"states={json.dumps(history)}")
    print(f"saved_path={saved_path}")
    return record, str(saved_path)


def main():
    run_id = uuid.uuid4().hex
    perform_run(run_id)


if __name__ == "__main__":
    main()
