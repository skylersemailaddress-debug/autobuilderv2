import sys
from dataclasses import asdict
from pathlib import Path
from datetime import datetime, timezone
import uuid
import json
import argparse

# Ensure top-level package imports work when executing cli/run.py directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from orchestrator.run_state_machine import RunStateMachine, RunState
from orchestrator.policy import RetryPolicy
from planner.planner import Planner
from planner.repo_context import inspect_repo_context
from execution.executor import Executor
from execution.artifacts import Artifact
from debugger.repair import RepairEngine
from debugger.classifier import FailureClassifier
from debugger.failures import FailureRecord
from control_plane.control import ControlDecision
from memory.store import MemoryStore
from memory.json_memory import JsonMemoryStore
from observability.events import create_event, event_to_dict
from runs.summary import build_run_summary
from state.checkpoints import create_checkpoint
from validator.contracts import (
    validate_plan_artifact,
    validate_task_result_artifact,
    validate_run_summary_contract,
)
from state.run_state import RunStateStore
from state.json_store import JsonRunStore
from state.resume import resume_run
from validator.confidence import calculate_confidence
from nexus.mode import NexusMode
from validator.validator import Validator
from control_plane.approvals import require_approval
from policies.action_policy import ActionPolicy
from planner.context import build_planning_context

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


def perform_run(run_id, goal=DEFAULT_GOAL, nexus_mode_enabled=False):
    created_at = datetime.now(timezone.utc).isoformat()
    nexus_config = NexusMode() if nexus_mode_enabled else None
    state_store = RunStateStore()
    run_sm = RunStateMachine()
    planner = Planner()
    executor = Executor()
    repair_engine = RepairEngine()
    validator = Validator()
    retry_policy = RetryPolicy(max_repairs=1)
    json_store = JsonRunStore(base_dir=ROOT_DIR / "runs")
    memory_store = MemoryStore()
    durable_memory_store = JsonMemoryStore(str(ROOT_DIR / "memory" / f"{run_id}.json"))
    action_policy = ActionPolicy()
    failure_classifier = FailureClassifier()

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
    failures = []
    events = [
        serialize_event(create_event("run_started", {"run_id": run_id})),
    ]

    # Query durable memory for relevant context
    memory_hits = durable_memory_store.search_memories(goal)
    memory_context = {hit["key"]: hit["value"] for hit in memory_hits}

    # Inspect repository for planning context
    repo_context = inspect_repo_context(ROOT_DIR)
    
    # Build planning context
    recent_summary = memory_context.get("summary")
    planning_context = build_planning_context(goal, memory_context, recent_summary, repo_context)
    
    # Create plan with context
    plan_result = planner.create_plan(goal, planning_context)
    tasks = plan_result["tasks"]
    plan_metadata = plan_result["metadata"]
    plan_artifact = plan_metadata.copy()
    
    events.append(serialize_event(create_event("plan_created", {"goal": goal, "task_count": len(tasks), "memory_used": plan_metadata["memory_used"]})))
    checkpoints.append(asdict(create_checkpoint("plan_created", {"task_count": len(tasks), "goal": goal, "memory_used": plan_metadata["memory_used"]})))

    # Classify action and create approval if needed
    policy = action_policy.classify_action(goal, [serialize_task(task) for task in tasks])
    control_decision = ControlDecision(
        action="run_execution",
        allowed=not policy["approval_required"],
        requires_pause=policy["approval_required"],
        reason=(
            f"Approval required for high-risk action: {goal}"
            if policy["approval_required"]
            else "Action allowed without operator pause"
        ),
    )

    approval_request = None
    if policy["approval_required"]:
        approval_request = require_approval("run_execution", f"High-risk action: {goal}")
        events.append(serialize_event(create_event("approval_requested", {
            "approval_id": approval_request.approval_id,
            "action": "run_execution",
            "reason": control_decision.reason,
        })))
        record = {
            "run_id": run_id,
            "created_at": created_at,
            "goal": goal,
            "status": "awaiting_approval",
            "state_history": history,
            "tasks": [serialize_task(task) for task in tasks],
            "artifacts": artifacts,
            "checkpoints": checkpoints,
            "confidence": 0.0,
            "policy": policy,
            "memory_context": memory_context,
            "repo_context": repo_context,
            "plan_artifact": plan_artifact,
            "memory_used": plan_metadata["memory_used"],
            "memory_hits": len(memory_hits),
            "plan_metadata": plan_metadata,
            "validation_result": None,
            "validation": None,
            "repair_used": repair_used,
            "repair_count": repair_count,
            "events": events,
            "failures": failures,
            "awaiting_approval": True,
            "control_state": asdict(control_decision),
            "nexus_mode": bool(nexus_config),
            "project_name": nexus_config.project_name if nexus_config else None,
            "approvals_enabled": nexus_config.approvals_enabled if nexus_config else False,
            "resumability_enabled": nexus_config.resumability_enabled if nexus_config else False,
            "memory_enabled": nexus_config.memory_enabled if nexus_config else False,
            "contract_validation_enabled": nexus_config.contract_validation_enabled if nexus_config else False,
        }
        if approval_request:
            record["approval_request"] = asdict(approval_request)
        record["summary"] = build_run_summary(record)
        plan_valid, plan_evidence = validate_plan_artifact(record["plan_artifact"])
        summary_valid, summary_evidence = validate_run_summary_contract(record["summary"])
        task_contracts = []
        for artifact in record["artifacts"]:
            if artifact.get("artifact_type") == "task_output":
                passed, evidence = validate_task_result_artifact(artifact)
                task_contracts.append({"artifact_id": artifact.get("artifact_id"), "passed": passed, "evidence": evidence})
        contract_validation_passed = plan_valid and summary_valid and all(item["passed"] for item in task_contracts)
        record["contract_validation_passed"] = contract_validation_passed
        record["contract_validation_results"] = {
            "plan": plan_evidence,
            "tasks": task_contracts,
            "summary": summary_evidence,
        }
        record["durable_memory_keys"] = durable_memory_store.list_keys()
        record["resume"] = resume_run(record)
        saved_path = json_store.save(run_id, record)

        print(f"run_id={run_id}")
        print(f"status={record['status']}")
        print(f"saved_path={saved_path}")
        return record, str(saved_path)

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
                # Classify the validation failure
                failure_record = failure_classifier.classify(validation_result)
                failures.append(asdict(failure_record))
                events.append(serialize_event(create_event("validation_failed", {
                    "validation": validation_result,
                    "failure_id": failure_record.failure_id,
                    "failure_type": failure_record.failure_type
                })))
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
        "policy": policy,
        "memory_context": memory_context,
        "repo_context": repo_context,
        "plan_artifact": plan_artifact,
        "memory_used": plan_metadata["memory_used"],
        "memory_hits": len(memory_hits),
        "plan_metadata": plan_metadata,
        "validation_result": validation_result,
        "validation": validation_result,
        "repair_used": repair_used,
        "repair_count": repair_count,
        "events": events,
        "failures": failures,
        "nexus_mode": bool(nexus_config),
        "project_name": nexus_config.project_name if nexus_config else None,
        "approvals_enabled": nexus_config.approvals_enabled if nexus_config else False,
        "resumability_enabled": nexus_config.resumability_enabled if nexus_config else False,
        "memory_enabled": nexus_config.memory_enabled if nexus_config else False,
        "contract_validation_enabled": nexus_config.contract_validation_enabled if nexus_config else False,
    }
    
    if approval_request:
        record["approval_request"] = asdict(approval_request)
    
    record["summary"] = build_run_summary(record)
    plan_valid, plan_evidence = validate_plan_artifact(record["plan_artifact"])
    summary_valid, summary_evidence = validate_run_summary_contract(record["summary"])
    task_contracts = []
    for artifact in record["artifacts"]:
        if artifact.get("artifact_type") == "task_output":
            passed, evidence = validate_task_result_artifact(artifact)
            task_contracts.append({"artifact_id": artifact.get("artifact_id"), "passed": passed, "evidence": evidence})
    contract_validation_passed = plan_valid and summary_valid and all(item["passed"] for item in task_contracts)
    record["contract_validation_passed"] = contract_validation_passed
    record["contract_validation_results"] = {
        "plan": plan_evidence,
        "tasks": task_contracts,
        "summary": summary_evidence,
    }
    memory_store.add_memory("summary", record["summary"])
    record["memory_keys"] = memory_store.list_keys()
    
    # Persist summary to durable memory
    durable_memory_store.add_memory("summary", record["summary"])
    record["durable_memory_keys"] = durable_memory_store.list_keys()
    
    # Add resume payload
    record["resume"] = resume_run(record)
    
    saved_path = json_store.save(run_id, record)

    print(f"run_id={run_id}")
    print(f"status={status}")
    print(f"states={json.dumps(history)}")
    print(f"saved_path={saved_path}")
    return record, str(saved_path)


def main():
    parser = argparse.ArgumentParser(description="Run AutobuilderV2")
    parser.add_argument(
        "--nexus",
        action="store_true",
        help="Enable Nexus0.5 mission mode for controlled autonomous execution",
    )
    args = parser.parse_args()

    run_id = uuid.uuid4().hex
    perform_run(run_id, nexus_mode_enabled=args.nexus)


if __name__ == "__main__":
    main()
