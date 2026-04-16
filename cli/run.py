import sys
from pathlib import Path
import uuid
import json

# Ensure top-level package imports work when executing cli/run.py directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from orchestrator.run_state_machine import RunStateMachine, RunState
from state.run_state import RunStateStore
from validator.validator import Validator


def perform_run(run_id):
    state_store = RunStateStore()
    run_sm = RunStateMachine()
    validator = Validator()

    history = [run_sm.state.value]
    state_store.save(run_id, run_sm.state.value)

    while run_sm.state not in (RunState.COMPLETE, RunState.FAILED):
        if run_sm.state == RunState.VALIDATE:
            success, _ = validator.validate({"run_id": run_id})
            next_state = run_sm.transition(success=success)
        else:
            next_state = run_sm.transition(success=True)

        state_store.save(run_id, next_state.value)
        history.append(next_state.value)

        if next_state == RunState.FAILED:
            break

    result = {
        "run_id": run_id,
        "status": run_sm.state.value,
        "state_history": history,
    }
    print(f"run_id={result['run_id']}")
    print(f"status={result['status']}")
    print(f"state_history={json.dumps(result['state_history'])}")
    return result


def main():
    run_id = uuid.uuid4().hex
    perform_run(run_id)


if __name__ == "__main__":
    main()
