import sys
from dataclasses import asdict
from pathlib import Path
from datetime import datetime, timezone
import json
import argparse
from typing import Dict

# Ensure top-level package imports work when executing cli/resume.py directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from orchestrator.run_state_machine import RunStateMachine, RunState
from orchestrator.policy import RetryPolicy
from planner.planner import Planner
from execution.executor import Executor
from execution.artifacts import Artifact
from debugger.repair import RepairEngine
from memory.store import MemoryStore
from memory.json_memory import JsonMemoryStore
from observability.events import create_event, event_to_dict
from runs.summary import build_run_summary
from state.checkpoints import create_checkpoint
from state.audit import append_audit_event, build_audit_record
from state.run_state import RunStateStore
from state.json_store import JsonRunStore
from state.resume_runner import infer_next_stage, resume_run
from validator.confidence import calculate_confidence
from validator.validator import Validator
from control_plane.approvals import ApprovalRequest
from policies.action_policy import ActionPolicy
from planner.task import Task


def serialize_task(task):
    return {
        "task_id": task.task_id,
        "title": task.title,
        "status": task.status,
        "result": task.result,
    }

def serialize_event(event):
    return event_to_dict(event)


def deserialize_task(task_dict):
    """Convert a serialized task dict back to a Task object."""
    return Task(
        task_id=task_dict["task_id"],
        title=task_dict["title"],
        status=task_dict["status"],
        result=task_dict.get("result")
    )


def resume_saved_run(run_id: str):
    """Resume a saved run from the inferred next stage."""
    json_store = JsonRunStore(base_dir=ROOT_DIR / "runs")
    
    # Load the saved record
    try:
        record = json_store.load(run_id)
    except FileNotFoundError:
        print(f"Error: Run record {run_id} not found")
        return None, None
    
    # If paused for approval, only resume after approval is granted.
    awaiting_approval = record.get("awaiting_approval", False)
    approval_request = record.get("approval_request")

    if awaiting_approval:
        if approval_request and approval_request.get("status") == "approved":
            print(f"Approval granted for run {run_id}, resuming execution")
            record["awaiting_approval"] = False
            record["control_state"] = record.get("control_state", {})
            record["audit_trail"] = append_audit_event(
                record.get("audit_trail", []),
                "resume_approved",
                actor="resume",
                details={"approval_id": approval_request.get("approval_id")},
            )
        elif approval_request and approval_request.get("status") == "denied":
            print(f"Run {run_id} cannot resume because approval was denied")
            return record, None
        else:
            print(f"Run {run_id} is awaiting approval and cannot resume yet")
            return record, None

    # Infer next stage and resume
    next_stage = infer_next_stage(record)
    if next_stage is None:
        print(f"Run {run_id} is already complete or failed, cannot resume")
        return record, None
    
    print(f"Resuming run {run_id} from stage: {next_stage}")
    
    # Continue execution from the next stage
    updated_record = continue_execution(record, next_stage)
    
    # Save the updated record
    saved_path = json_store.save(run_id, updated_record)
    
    print(f"Resumed run saved to: {saved_path}")
    return updated_record, str(saved_path)


def continue_execution(record: Dict, next_stage: str) -> Dict:
    """Continue execution from the specified stage."""
    # Reconstruct state from record
    run_id = record["run_id"]
    goal = record["goal"]
    
    # Initialize components
    state_store = RunStateStore()
    run_sm = RunStateMachine()
    planner = Planner()
    executor = Executor()
    repair_engine = RepairEngine()
    validator = Validator()
    retry_policy = RetryPolicy(max_repairs=1)
    memory_store = MemoryStore()
    durable_memory_store = JsonMemoryStore(str(ROOT_DIR / "memory" / f"{run_id}.json"))
    action_policy = ActionPolicy()
    
    # Restore state from record
    tasks = [deserialize_task(task) for task in record.get("tasks", [])]
    checkpoints = record.get("checkpoints", [])
    events = record.get("events", [])
    validation_result = record.get("validation_result")
    repair_count = record.get("repair_count", 0)
    
    # Set the state machine to the appropriate state
    if next_stage == "plan":
        run_sm.state = RunState.INTAKE
    elif next_stage == "execute":
        run_sm.state = RunState.EXECUTE
    elif next_stage == "repair":
        run_sm.state = RunState.REPAIR
    
    # Continue from the next stage
    while run_sm.state not in (RunState.COMPLETE, RunState.FAILED):
        if run_sm.state == RunState.EXECUTE and next_stage == "execute":
            # Continue execution of incomplete tasks
            events.append(serialize_event(create_event("execution_resumed", {"task_count": len(tasks)})))
            tasks = executor.run_tasks(tasks)
            events.append(serialize_event(create_event("execution_completed", {"task_count": len(tasks)})))
            checkpoints.append(asdict(create_checkpoint("execution_completed", {"task_count": len(tasks)})))
            next_stage = None  # Mark as processed
        elif run_sm.state == RunState.VALIDATE:
            success, validation_result = validator.validate(tasks)
            if success:
                events.append(serialize_event(create_event("validation_passed", {"task_count": len(tasks)})))
                run_sm.transition(success=True)
            else:
                events.append(serialize_event(create_event("validation_failed", {"validation": validation_result})))
                if retry_policy.can_retry(repair_count):
                    run_sm.transition(success=False)
                else:
                    run_sm.state = RunState.FAILED
        elif run_sm.state == RunState.REPAIR and next_stage == "repair":
            events.append(serialize_event(create_event("repair_resumed", {"repair_count": repair_count + 1})))
            tasks = repair_engine.repair_tasks(tasks)
            repair_count += 1
            events.append(serialize_event(create_event("repair_completed", {"repair_count": repair_count})))
            next_stage = None  # Mark as processed
            run_sm.transition(success=True)
        else:
            # For other states, just transition normally
            run_sm.transition(success=True)
        
        if run_sm.state == RunState.FAILED:
            break
    
    # Update the record with resumed execution
    record["resumed"] = True
    record["resumed_from"] = next_stage or "unknown"
    record["tasks"] = [serialize_task(task) for task in tasks]
    record["checkpoints"] = checkpoints
    record["events"] = events
    record["validation_result"] = validation_result
    record["repair_count"] = repair_count
    
    # Recalculate artifacts and summary
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
    record["artifacts"] = artifacts
    
    if run_sm.state == RunState.COMPLETE:
        events.append(serialize_event(create_event("run_completed", {"status": "complete"})))
    else:
        events.append(serialize_event(create_event("run_completed", {"status": "failed"})))
    
    record["status"] = run_sm.state.value
    record["summary"] = build_run_summary(record)
    restore_payload = record.get("restore_payload") or {}
    record["audit_record"] = build_audit_record(
        "resume",
        outcome=record.get("status", "unknown"),
        run_id=run_id,
        risk_level=(record.get("policy") or {}).get("risk_level", "low"),
        approval_state=(record.get("approval_request") or {}).get("status", "not_required"),
        checkpoint_ids=[item.get("checkpoint_id") for item in checkpoints if item.get("checkpoint_id")],
        rollback_ready=bool(restore_payload.get("restore_possible")),
        restore_checkpoint_id=restore_payload.get("checkpoint_id"),
        actor="resume",
        details={"resumed_from": record.get("resumed_from")},
    )
    
    # Update memory
    memory_store.add_memory("summary", record["summary"])
    record["memory_keys"] = memory_store.list_keys()
    
    durable_memory_store.add_memory("summary", record["summary"])
    record["durable_memory_keys"] = durable_memory_store.list_keys()
    record["audit_trail"] = append_audit_event(
        record.get("audit_trail", []),
        "resume_completed",
        actor="resume",
        details={"status": record.get("status")},
    )
    
    return record


def main():
    parser = argparse.ArgumentParser(description="Resume an interrupted AutobuilderV2 run")
    parser.add_argument("run_id", help="The run ID to resume")
    
    args = parser.parse_args()
    
    record, saved_path = resume_saved_run(args.run_id)
    if record:
        print(f"Run {args.run_id} resumed successfully")
        print(f"Final status: {record.get('status')}")


if __name__ == "__main__":
    main()
