from typing import Dict


def build_run_summary(record: Dict) -> Dict:
    tasks = record.get("tasks", [])
    events = record.get("events", [])
    failures = record.get("failures", [])
    completed_tasks = sum(1 for task in tasks if task.get("status") == "complete")

    repo_context = record.get("repo_context", {})
    repo_signals = {
        "framework_hints": repo_context.get("framework_hints", []),
        "config_files": repo_context.get("config_files", []),
        "test_folders": repo_context.get("test_folders", []),
    }

    return {
        "run_id": record.get("run_id"),
        "goal": record.get("goal"),
        "final_status": record.get("status"),
        "repair_used": record.get("repair_used", False),
        "repair_count": record.get("repair_count", 0),
        "total_tasks": len(tasks),
        "completed_tasks": completed_tasks,
        "event_count": len(events),
        "confidence": record.get("confidence", 0.0),
        "checkpoint_count": len(record.get("checkpoints", [])),
        "artifact_count": len(record.get("artifacts", [])),
        "risk_level": record.get("policy", {}).get("risk_level", "unknown"),
        "approval_required": record.get("policy", {}).get("approval_required", False),
        "memory_used": record.get("memory_used", False),
        "memory_hits": record.get("memory_hits", 0),
        "failure_count": len(failures),
        "failure_types": list(set(f.get("failure_type", "unknown") for f in failures)),
        "critical_failures": sum(1 for f in failures if f.get("severity") == "critical"),
        "repo_mode": bool(repo_context),
        "repo_signals": repo_signals,
    }
