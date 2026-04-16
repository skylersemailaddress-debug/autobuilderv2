import sys
from dataclasses import asdict
from pathlib import Path
from datetime import datetime, timezone
import uuid
import json

# Ensure top-level package imports work when executing cli/run.py directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from orchestrator.run_state_machine import RunStateMachine, RunState
from orchestrator.policy import RetryPolicy
from planner.planner import Planner
from execution.executor import Executor
from execution.artifacts import Artifact
from debugger.repair import RepairEngine
from memory.store import MemoryStore
from observability.events import create_event, event_to_dict
from runs.summary import build_run_summary
from state.checkpoints import create_checkpoint
from state.run_state import RunStateStore
from state.json_store import JsonRunStore
from validator.confidence import calculate_confidence
from validator.validator import Validator

DEFAULT_GOAL = "Build an autonomous execution plan"


def serialize_task(task):
    return {
        "task_id": task.task_id,
        "title": task.title,
        "status": task.status,
        "result": task.result,
    }

def serialize_event(event):
    return event_to_dict(event)


def perform_run(run_id, goal=DEFAULT_GOAL):
    created_at = datetime.now(timezone.utc).isoformat()
    state_store = RunStateStore()
    run_sm = RunStateMachine()
    planner = Planner()
    executor = Executor()
    repair_engine = RepairEngine()
    validator = Validator()
    retry_policy = RetryPolicy(max_repairs=1)
    json_store = JsonRunStore(base_dir=ROOT_DIR / "runs")
    memory_store = MemoryStore()

    memory_store.add_memory("goal", {"goal": goal})
    checkpoints = [
        asdict(create_checkpoint("start", {"run_id": run_id})),
    ]

    history = [run_sm.state.value]
    state_store.save(run_id, run_sm.state.value)
    artifacts = []
    validation_result = None
    repair_used = False
    repair_count = 0
    events = [
        serialize_event(create_event("run_started", {"run_id": run_id})),
    ]

    tasks = planner.create_plan(goal)
    events.append(serialize_event(create_event("plan_created", {"goal": goal, "task_count": len(tasks)})))
    checkpoints.append(asdict(create_checkpoint("plan_created", {"task_count": len(tasks), "goal": goal})))

    events.append(serialize_event(create_event("execution_started", {"task_count": len(tasks)})))
    tasks = executor.run_tasks(tasks)
    events.append(serialize_event(create_event("execution_completed", {"task_count": len(tasks)})))

    artifacts = [
        asdict(
            Artifact(
                artifact_id=task.task_id,
                artifact_type="task_output",
                content=task.result,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        for task in tasks
        if task.result is not None
    ]
    checkpoints.append(asdict(create_checkpoint("execution_completed", {"task_count": len(tasks)})))

    # Intentionally leave one task incomplete to exercise the repair loop.
    if tasks:
        tasks[0].status = "pending"
        tasks[0].result = None

    while run_sm.state not in (RunState.COMPLETE, RunState.FAILED):
        if run_sm.state == RunState.VALIDATE:
            success, validation_result = validator.validate(tasks)
            if success:
                events.append(serialize_event(create_event("validation_passed", {"task_count": len(tasks)})))
                next_state = run_sm.transition(success=True)
            else:
                events.append(serialize_event(create_event("validation_failed", {"validation": validation_result})))
                if retry_policy.can_retry(repair_count):
                    next_state = run_sm.transition(success=False)
                else:
                    run_sm.state = RunState.FAILED
                    next_state = run_sm.state
        elif run_sm.state == RunState.REPAIR:
            events.append(serialize_event(create_event("repair_started", {"repair_count": repair_count + 1})))
            tasks = repair_engine.repair_tasks(tasks)
            repair_used = True
            repair_count += 1
            events.append(serialize_event(create_event("repair_completed", {"repair_count": repair_count})))
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

    if run_sm.state == RunState.COMPLETE:
        events.append(serialize_event(create_event("run_completed", {"status": "complete"})))
    else:
        events.append(serialize_event(create_event("run_completed", {"status": "failed"})))

    status = run_sm.state.value
    checkpoints.append(asdict(create_checkpoint("run_completed", {"status": status})))

    confidence = calculate_confidence(tasks, validation_result, repair_count)
    record = {
        "run_id": run_id,
        "created_at": created_at,
        "goal": goal,
        "status": status,
        "state_history": history,
        "tasks": [serialize_task(task) for task in tasks],
        "artifacts": artifacts,
        "checkpoints": checkpoints,
        "confidence": confidence,
        "validation_result": validation_result,
        "validation": validation_result,
        "repair_used": repair_used,
        "repair_count": repair_count,
        "events": events,
    }
    record["summary"] = build_run_summary(record)
    memory_store.add_memory("summary", record["summary"])
    record["memory_keys"] = memory_store.list_keys()
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
