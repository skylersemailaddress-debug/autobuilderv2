import sys
from pathlib import Path
from datetime import datetime, timezone
import uuid
import json

# Ensure top-level package imports work when executing cli/run.py directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from orchestrator.run_state_machine import RunStateMachine, RunState
from planner.planner import Planner
from execution.executor import Executor
from debugger.repair import RepairEngine
from state.run_state import RunStateStore
from state.json_store import JsonRunStore
from validator.validator import Validator

DEFAULT_GOAL = "Build an autonomous execution plan"


def serialize_task(task):
    return {
        "task_id": task.task_id,
        "title": task.title,
        "status": task.status,
        "result": task.result,
    }


def perform_run(run_id, goal=DEFAULT_GOAL):
    created_at = datetime.now(timezone.utc).isoformat()
    state_store = RunStateStore()
    run_sm = RunStateMachine()
    planner = Planner()
    executor = Executor()
    repair_engine = RepairEngine()
    validator = Validator()
    json_store = JsonRunStore(base_dir=ROOT_DIR / "runs")

    history = [run_sm.state.value]
    state_store.save(run_id, run_sm.state.value)
    artifacts = [{"state": run_sm.state.value, "timestamp": created_at}]
    validation_result = None
    repair_used = False

    tasks = planner.create_plan(goal)
    tasks = executor.run_tasks(tasks)

    # Intentionally leave one task incomplete to exercise the repair loop.
    if tasks:
        tasks[0].status = "pending"
        tasks[0].result = None

    artifacts.extend([task.result for task in tasks if task.result is not None])

    while run_sm.state not in (RunState.COMPLETE, RunState.FAILED):
        if run_sm.state == RunState.VALIDATE:
            success, validation_result = validator.validate(tasks)
            next_state = run_sm.transition(success=success)
        elif run_sm.state == RunState.REPAIR:
            tasks = repair_engine.repair_tasks(tasks)
            repair_used = True
            next_state = run_sm.transition(success=True)
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
        "goal": goal,
        "status": status,
        "state_history": history,
        "tasks": [serialize_task(task) for task in tasks],
        "artifacts": artifacts,
        "validation_result": validation_result,
        "validation": validation_result,
        "repair_used": repair_used,
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
